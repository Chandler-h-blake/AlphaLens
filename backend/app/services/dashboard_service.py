from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path

from sqlalchemy import select

from app.core.config import Settings, get_settings
from app.core.exceptions import ResourceNotFoundError
from app.db.models import WorkspaceSnapshot
from app.db.session import get_session_factory
from app.market.public_snapshots import PublicDashboardProvider
from app.market.eastmoney_provider import EastMoneyPublicProvider
from app.schemas.dashboard import SnapshotResponse
from app.services.factor_service import FactorService


class DashboardService:
    """Persisted dashboard/fund snapshots with seed-data fallback."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        if not self.settings.database_url:
            raise RuntimeError("仪表盘快照需要配置 DATABASE_URL。")
        self.session_factory = get_session_factory(self.settings.database_url)

    def get(self, key: str) -> SnapshotResponse:
        with self.session_factory() as session:
            item = session.scalar(select(WorkspaceSnapshot).where(WorkspaceSnapshot.key == key))
        if item is None:
            raise ResourceNotFoundError(f"未找到 {key} 快照。")
        age = datetime.now() - item.fetched_at
        return SnapshotResponse(
            data=item.payload, source=item.source, as_of=item.as_of, fetched_at=item.fetched_at,
            freshness="stale" if age > timedelta(minutes=30) or "演示" in item.source else "cached",
            warning="合成演示数据，不代表任何交易日的真实行情。" if "演示" in item.source else ("当前展示的是历史快照，请手动刷新。" if age > timedelta(minutes=30) else None),
        )

    def refresh(self, key: str) -> SnapshotResponse:
        current = self.get(key)
        try:
            if self.settings.market_data_provider == "disabled":
                raise RuntimeError("在线数据源已禁用")
            data, source, as_of = PublicDashboardProvider(self.settings.market_data_timeout_seconds).fetch(key)
            return self._save(key, data, source, as_of)
        except Exception as error:
            if key == "dashboard":
                try:
                    data, source, as_of = self._fetch_research_pool_dashboard()
                    return self._save(
                        key, data, source, as_of,
                        warning="全市场主接口不可用；当前展示四大指数和 30 只研究候选股范围统计。",
                    )
                except Exception as fallback_error:
                    error = RuntimeError(f"主源：{error}；备用源：{fallback_error}")
            return current.model_copy(update={"freshness": "stale", "warning": f"公开数据刷新失败，已保留最近一次成功快照：{error}"})

    def _save(self, key: str, data: dict, source: str, as_of: datetime, warning: str | None = None) -> SnapshotResponse:
        now = datetime.now()
        with self.session_factory.begin() as session:
            item = session.get(WorkspaceSnapshot, key)
            item.payload, item.source, item.as_of, item.fetched_at = data, source, as_of, now
        return SnapshotResponse(data=data, source=source, as_of=as_of, fetched_at=now, freshness="fresh", warning=warning)

    def _fetch_research_pool_dashboard(self) -> tuple[dict, str, datetime]:
        candidates = FactorService().get_top_pool(keyword=None, industry=None, limit=30).items
        provider = EastMoneyPublicProvider(self.settings)
        with ThreadPoolExecutor(max_workers=6) as executor:
            quotes = list(executor.map(provider.fetch_quote, [item.symbol for item in candidates]))
            indexes = list(executor.map(provider.fetch_index_quote, ["sh000001", "sz399001", "sz399006", "sh000688"]))
        if len(quotes) != len(candidates) or len(indexes) != 4:
            raise RuntimeError("候选池备用行情不完整。")
        industries: dict[str, list[float]] = {}
        industry_by_symbol = {item.symbol: item.industry for item in candidates}
        for quote in quotes:
            if quote.change_percent is not None:
                industries.setdefault(industry_by_symbol[quote.symbol], []).append(quote.change_percent)
        changes = [quote.change_percent for quote in quotes]
        as_of_values = [quote.as_of for quote in quotes] + [item["as_of"] for item in indexes]
        data = {
            "indexes": [{key: value for key, value in item.items() if key != "as_of"} for item in indexes],
            "industries": sorted(
                ({"name": name, "change_percent": sum(values) / len(values)} for name, values in industries.items()),
                key=lambda item: item["change_percent"], reverse=True,
            ),
            "distribution": {
                "up": sum(value is not None and value > 0 for value in changes),
                "down": sum(value is not None and value < 0 for value in changes),
                "flat": sum(value == 0 for value in changes),
                "limit_up": None, "limit_down": None,
                "note": "涨跌分布仅统计当前研究候选池，不代表全市场。",
            },
            "top_turnover": [
                {"symbol": item.symbol, "name": item.name, "change_percent": item.change_percent or 0, "amount": item.amount or 0}
                for item in sorted(quotes, key=lambda quote: quote.amount or 0, reverse=True)[:20]
            ],
        }
        # Use the oldest component timestamp so the combined snapshot never claims to be newer than any input.
        return data, "腾讯财经公开行情（当前 30 只研究候选股范围）", min(as_of_values)

    @staticmethod
    def seed_if_missing(database_url: str, seed_dir: Path) -> None:
        factory = get_session_factory(database_url)
        now = datetime.now()
        seed_files = {"dashboard": seed_dir / "dashboard.json", "funds": seed_dir / "funds.json"}
        with factory.begin() as session:
            for key, path in seed_files.items():
                if session.scalar(select(WorkspaceSnapshot).where(WorkspaceSnapshot.key == key)) is not None:
                    continue
                session.add(WorkspaceSnapshot(key=key, payload=json.loads(path.read_text(encoding="utf-8")), source="合成演示数据（非真实行情）", as_of=datetime(2026, 1, 1), fetched_at=now))
