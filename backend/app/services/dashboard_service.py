from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

from sqlalchemy import select

from app.core.config import Settings, get_settings
from app.core.exceptions import ResourceNotFoundError
from app.db.models import WorkspaceSnapshot
from app.db.session import get_session_factory
from app.market.public_snapshots import PublicDashboardProvider
from app.schemas.dashboard import SnapshotResponse


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
            now = datetime.now()
            with self.session_factory.begin() as session:
                item = session.get(WorkspaceSnapshot, key)
                item.payload, item.source, item.as_of, item.fetched_at = data, source, as_of, now
            return SnapshotResponse(data=data, source=source, as_of=as_of, fetched_at=now, freshness="fresh")
        except Exception as error:
            return current.model_copy(update={"freshness": "stale", "warning": f"公开数据刷新失败，已保留最近一次成功快照：{error}"})

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
