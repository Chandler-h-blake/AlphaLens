from datetime import date, datetime

import pandas as pd
from sqlalchemy import select

from app.core.exceptions import ResourceNotFoundError
from app.db.models import FactorOverview, FactorScore, IndustryRotation, ResearchReport, Stock
from app.db.session import get_session_factory
from app.repositories.research_repository import ResearchReportRecord


class DatabaseRepository:
    """Database-backed repository for runtime snapshots and reports."""

    def __init__(self, database_url: str) -> None:
        self.session_factory = get_session_factory(database_url)

    def get_top_pool(self) -> pd.DataFrame:
        with self.session_factory() as session:
            rows = session.execute(
                select(FactorScore, Stock)
                .join(Stock, FactorScore.symbol == Stock.symbol)
                .order_by(FactorScore.data_date.desc(), FactorScore.rank, Stock.symbol)
            ).all()
        if not rows:
            return pd.DataFrame(columns=["rank", "symbol", "name", "industry", "composite_score"])
        latest_date = rows[0].FactorScore.data_date
        records = []
        for score, stock in rows:
            if score.data_date != latest_date:
                continue
            records.append({"rank": score.rank, "symbol": stock.symbol, "name": stock.name, "industry": stock.industry or "unknown", "composite_score": score.composite_score, **score.factor_values})
        return pd.DataFrame(records)

    def get_overview(self) -> pd.DataFrame:
        with self.session_factory() as session:
            rows = session.scalars(select(FactorOverview).order_by(FactorOverview.data_date.desc(), FactorOverview.weight.desc())).all()
        if not rows:
            return pd.DataFrame()
        latest_date = rows[0].data_date
        return pd.DataFrame([{
            "factor": row.factor, "name": row.name, "category": row.category, "direction": row.direction,
            "direction_text": row.direction_text, "weight": row.weight, "data_source": row.data_source,
            "description": row.description, **row.metrics,
        } for row in rows if row.data_date == latest_date])

    def list_reports(self) -> list[ResearchReportRecord]:
        with self.session_factory() as session:
            rows = session.scalars(select(ResearchReport).order_by(ResearchReport.generated_at.desc())).all()
        return [self._to_report_record(row) for row in rows]

    def get_report(self, symbol: str) -> ResearchReportRecord:
        with self.session_factory() as session:
            row = session.scalar(select(ResearchReport).where(ResearchReport.symbol == symbol).order_by(ResearchReport.generated_at.desc()))
        if row is None:
            raise ResourceNotFoundError(f"未找到股票代码 {symbol} 的研究报告。")
        return self._to_report_record(row)

    def get_rotation(self) -> pd.DataFrame:
        with self.session_factory() as session:
            rows = session.scalars(select(IndustryRotation).order_by(IndustryRotation.data_date.desc(), IndustryRotation.rank_1m)).all()
        if not rows:
            return pd.DataFrame()
        latest_date = rows[0].data_date
        return pd.DataFrame([{
            "industry_code": row.industry_code, "industry_name": row.industry_name, "last_date": row.data_date.isoformat(),
            "latest_close": row.latest_close, "return_1m": row.return_1m, "return_3m": row.return_3m,
            "rank_1m": row.rank_1m, "rank_3m": row.rank_3m, "rotation_type": row.rotation_type,
            "generated_at": row.generated_at.isoformat(sep=" ") if row.generated_at else "",
        } for row in rows if row.data_date == latest_date])

    @staticmethod
    def _to_report_record(row: ResearchReport) -> ResearchReportRecord:
        return ResearchReportRecord(
            symbol=row.symbol,
            name=row.name,
            title=row.title,
            industry=row.industry,
            generated_at=row.generated_at,
            content_markdown=row.content_markdown,
            source_file=row.source_file or "database",
            sources=row.sources,
        )
