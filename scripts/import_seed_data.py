"""Import the bundled AlphaLens seed snapshots into PostgreSQL."""

from __future__ import annotations

import argparse
from datetime import date, datetime
from pathlib import Path
import sys

import pandas as pd
from sqlalchemy import delete, func, select


ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.db.base import Base  # noqa: E402
from app.db.models import FactorOverview, FactorScore, IndustryRotation, ResearchReport, Stock, WorkspaceSnapshot  # noqa: E402
from app.db.session import get_engine, get_session_factory  # noqa: E402
from app.repositories.industry_repository import IndustryRepository  # noqa: E402
from app.repositories.research_repository import ResearchRepository  # noqa: E402
from app.services.dashboard_service import DashboardService  # noqa: E402


FACTOR_DIR = ROOT / "data" / "seed" / "factors"
REPORT_DIR = ROOT / "data" / "seed" / "research" / "reports"
INDUSTRY_FILE = ROOT / "data" / "seed" / "industry" / "industry_rotation.csv"
INDUSTRY_MAPPING_FILE = ROOT / "data" / "seed" / "research" / "industry_mapping.csv"
CORE_COLUMNS = {"rank", "symbol", "name", "industry", "composite_score"}
METRIC_COLUMNS = {
    "spearman_ic_adjusted", "pearson_ic_adjusted", "ic_positive_rate", "group1_minus_group5",
    "group_spread_positive_rate", "validation_n", "snapshot_count",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-url", required=True)
    parser.add_argument("--data-date", default="2026-07-07")
    parser.add_argument("--factor-dir", type=Path, default=FACTOR_DIR)
    parser.add_argument("--report-dir", type=Path, default=REPORT_DIR)
    parser.add_argument("--industry-file", type=Path, default=INDUSTRY_FILE)
    parser.add_argument("--industry-mapping-file", type=Path, default=INDUSTRY_MAPPING_FILE)
    parser.add_argument("--replace", action="store_true", help="刷新因子和行业历史数据，保留 AI 生成报告与任务记录。")
    return parser.parse_args()


def clean_number(value: object) -> float | int | None:
    return None if pd.isna(value) else float(value)


def main() -> int:
    args = parse_args()
    data_date = date.fromisoformat(args.data_date)
    engine = get_engine(args.database_url)
    Base.metadata.create_all(engine)
    DashboardService.seed_if_missing(args.database_url, ROOT / "data" / "seed")
    session_factory = get_session_factory(args.database_url)

    with session_factory() as session:
        score_count = session.scalar(select(func.count()).select_from(FactorScore)) or 0
    if score_count and not args.replace:
        print("检测到已导入的历史数据，跳过初始化。使用 --replace 可刷新因子和行业数据。")
        return 0

    top_pool = pd.read_csv(args.factor_dir / "final_top30_stock_pool.csv", dtype={"symbol": str}, encoding="utf-8-sig")
    scores_path = args.factor_dir / 'final_factor_scores.csv'
    if scores_path.exists():
        full = pd.read_csv(scores_path, dtype={'symbol': str}, encoding='utf-8-sig')
        columns = ['symbol'] + [c for c in full.columns if c.endswith('_weighted_score')]
        top_pool = top_pool.merge(full[columns], on='symbol', how='left', validate='one_to_one')
    overview = pd.read_csv(args.factor_dir / "final_factor_overview.csv", encoding="utf-8-sig")
    reports = ResearchRepository(args.report_dir).list_reports()
    rotation = IndustryRepository(args.industry_file).get_rotation()
    report_industries = {report.symbol: report.industry for report in reports}
    mapping = pd.read_csv(args.industry_mapping_file, dtype={"symbol": str}, encoding="utf-8-sig")
    mapped_industries = mapping.set_index("symbol")["industry"].to_dict()

    with session_factory.begin() as session:
        if args.replace:
            # Historical refreshes must not erase reports created by the LLM workflow.
            for model in (IndustryRotation, FactorOverview, FactorScore):
                session.execute(delete(model))
            session.execute(delete(WorkspaceSnapshot).where(WorkspaceSnapshot.key == "factor_refresh"))
        existing_source_files = set(session.scalars(select(ResearchReport.source_file)).all())
        for record in top_pool.to_dict("records"):
            symbol = str(record["symbol"]).zfill(6)
            original_industry = str(record["industry"])
            industry = report_industries.get(symbol) or mapped_industries.get(symbol) or original_industry
            session.merge(Stock(symbol=symbol, name=str(record["name"]), industry=industry))
        # PostgreSQL enforces this foreign key immediately; persist stock masters first.
        session.flush()
        for record in top_pool.to_dict("records"):
            symbol = str(record["symbol"]).zfill(6)
            factor_values = {key: clean_number(value) for key, value in record.items() if key not in CORE_COLUMNS}
            session.add(FactorScore(symbol=symbol, data_date=data_date, rank=int(record["rank"]), composite_score=float(record["composite_score"]), factor_values=factor_values))
        for record in overview.to_dict("records"):
            metrics = {key: clean_number(record.get(key)) for key in METRIC_COLUMNS}
            session.add(FactorOverview(factor=str(record["factor"]), data_date=data_date, name=str(record["name"]), category=str(record["category"]), direction=int(record["direction"]), direction_text=str(record["direction_text"]), weight=float(record["weight"]), data_source=str(record["data_source"]), description=str(record["description"]), metrics=metrics))
        for report in reports:
            if report.source_file in existing_source_files:
                continue
            session.add(ResearchReport(symbol=report.symbol, name=report.name, title=report.title, industry=report.industry, generated_at=report.generated_at, content_markdown=report.content_markdown, sources=[{"name": "AlphaLens 多因子评分快照", "type": "internal_data", "as_of": None}, {"name": report.source_file, "type": "seed_markdown_report", "as_of": None}], source_file=report.source_file))
        for record in rotation.to_dict("records"):
            session.add(IndustryRotation(industry_code=str(record["industry_code"]), data_date=date.fromisoformat(str(record["last_date"])), industry_name=str(record["industry_name"]), latest_close=clean_number(record.get("latest_close")), return_1m=float(record["return_1m"]), return_3m=float(record["return_3m"]), rank_1m=int(record["rank_1m"]), rank_3m=int(record["rank_3m"]), rotation_type=str(record["rotation_type"]), generated_at=datetime.strptime(str(record["generated_at"]), "%Y-%m-%d %H:%M:%S")))

    print(f"已导入：{len(top_pool)} 个因子评分、{len(overview)} 个因子概览、{len(reports)} 份报告、{len(rotation)} 条行业轮动记录。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
