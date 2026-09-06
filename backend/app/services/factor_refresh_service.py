from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime
from math import sqrt
from typing import Protocol
from uuid import uuid4

import pandas as pd
from fastapi import BackgroundTasks
from sqlalchemy import delete, select

from app.core.config import Settings, get_settings
from app.core.exceptions import MarketDataProviderError, ResourceNotFoundError
from app.db.models import FactorScore, ResearchTask, Stock, WorkspaceSnapshot
from app.db.session import get_session_factory
from app.market.eastmoney_provider import DailyBar, EastMoneyPublicProvider
from app.repositories.database_repository import DatabaseRepository
from app.schemas.factors import FactorRefreshTaskResponse


TECHNICAL_FACTORS = {"momentum_20d", "turnover_change", "volatility_60d"}


class DailyHistoryProvider(Protocol):
    def fetch_daily_history(self, symbol: str, limit: int = 90) -> list[DailyBar]: ...


class FactorRefreshService:
    """Refresh market-sensitive factors and atomically publish a new candidate-pool ranking."""

    def __init__(self, settings: Settings | None = None, provider: DailyHistoryProvider | None = None) -> None:
        self.settings = settings or get_settings()
        if self.settings.data_backend != "database" or not self.settings.database_url:
            raise RuntimeError("因子在线刷新需要 PostgreSQL 数据源。")
        self.factory = get_session_factory(self.settings.database_url)
        self.repository = DatabaseRepository(self.settings.database_url)
        self.provider = provider or EastMoneyPublicProvider(self.settings)

    def create(self, background_tasks: BackgroundTasks) -> FactorRefreshTaskResponse:
        with self.factory.begin() as session:
            active = session.scalar(
                select(ResearchTask).where(
                    ResearchTask.kind == "factor_refresh",
                    ResearchTask.status.in_(["pending", "running"]),
                )
            )
            if active is not None:
                return self._response(active)
            task = ResearchTask(
                id=str(uuid4()), symbol="", kind="factor_refresh", status="pending", created_at=datetime.now()
            )
            session.add(task)
        background_tasks.add_task(self._run, task.id)
        return self._response(task)

    def get(self, task_id: str) -> FactorRefreshTaskResponse:
        with self.factory() as session:
            task = session.get(ResearchTask, task_id)
            if task is None or task.kind != "factor_refresh":
                raise ResourceNotFoundError("未找到因子刷新任务。")
            return self._response(task)

    def _run(self, task_id: str) -> None:
        self._set_task(task_id, status="running")
        try:
            source = self.repository.get_top_pool()
            overview = self.repository.get_overview()
            if source.empty or len(source) < 2:
                raise ValueError("候选池数据不足，无法进行截面标准化。")
            symbols = source["symbol"].astype(str).tolist()
            with ThreadPoolExecutor(max_workers=min(6, len(symbols))) as executor:
                histories = dict(zip(symbols, executor.map(self.provider.fetch_daily_history, symbols)))
            common_date = self._latest_common_date(histories)
            refreshed = self._calculate(source, overview, histories, common_date)
            history_sources = sorted({bar.source for bars in histories.values() for bar in bars})
            self._publish(refreshed, common_date, " + ".join(history_sources))
            self._set_task(task_id, status="succeeded", finished_at=datetime.now(), error_message=None)
        except Exception as error:
            self._set_task(task_id, status="failed", finished_at=datetime.now(), error_message=str(error)[:2000])

    @staticmethod
    def _latest_common_date(histories: dict[str, list[DailyBar]]) -> date:
        common_dates: set[date] | None = None
        for bars in histories.values():
            dates = {bar.trading_date for bar in bars}
            common_dates = dates if common_dates is None else common_dates.intersection(dates)
        if not common_dates:
            raise MarketDataProviderError("候选股票没有共同的有效交易日，未发布新排名。")
        return max(common_dates)

    @staticmethod
    def _calculate(
        source: pd.DataFrame,
        overview: pd.DataFrame,
        histories: dict[str, list[DailyBar]],
        common_date: date,
    ) -> pd.DataFrame:
        weights = dict(zip(overview["factor"], overview["weight"]))
        directions = dict(zip(overview["factor"], overview["direction"]))
        if len(weights) != 9 or set(weights) != set(directions) or abs(sum(weights.values()) - 1) > 1e-8:
            raise ValueError("九因子权重配置不完整或权重之和不为 1。")
        records = []
        for row in source.to_dict("records"):
            symbol = str(row["symbol"])
            bars = [bar for bar in histories[symbol] if bar.trading_date <= common_date]
            if len(bars) < 61:
                raise MarketDataProviderError(f"{symbol} 在共同交易日前的有效日线不足 61 条。")
            closes = pd.Series([bar.close for bar in bars], dtype=float)
            turnover = pd.Series([bar.turnover_rate for bar in bars], dtype=float)
            average_20d = turnover.iloc[-20:].mean()
            if average_20d <= 0:
                raise MarketDataProviderError(f"{symbol} 最近 20 日换手率无效。")
            row.update(
                momentum_20d=float(closes.iloc[-1] / closes.iloc[-21] - 1),
                turnover_change=float(turnover.iloc[-5:].mean() / average_20d - 1),
                volatility_60d=float(closes.pct_change().dropna().iloc[-60:].std(ddof=0) * sqrt(252)),
            )
            records.append(row)
        frame = pd.DataFrame(records)
        contribution_columns = []
        for factor, weight in weights.items():
            values = pd.to_numeric(frame[factor], errors="coerce")
            if values.isna().any():
                raise ValueError(f"{factor} 存在缺失值，未发布新排名。")
            standard_deviation = values.std(ddof=0)
            standardized = (values - values.mean()) / standard_deviation if standard_deviation > 0 else values * 0
            contribution = f"{factor}_weighted_score"
            frame[contribution] = standardized * float(directions[factor]) * float(weight)
            contribution_columns.append(contribution)
        frame["composite_score"] = frame[contribution_columns].sum(axis=1)
        frame = frame.sort_values(["composite_score", "symbol"], ascending=[False, True]).reset_index(drop=True)
        frame["rank"] = frame.index + 1
        return frame

    def _publish(self, frame: pd.DataFrame, data_date: date, history_source: str) -> None:
        now = datetime.now()
        factor_names = set(self.repository.get_overview()["factor"].tolist())
        with self.factory.begin() as session:
            session.execute(delete(FactorScore).where(FactorScore.data_date == data_date))
            for row in frame.to_dict("records"):
                session.merge(Stock(symbol=str(row["symbol"]), name=str(row["name"]), industry=str(row["industry"])))
            session.flush()
            for row in frame.to_dict("records"):
                values = {
                    key: float(value)
                    for key, value in row.items()
                    if key in factor_names or key.endswith("_weighted_score")
                }
                session.add(
                    FactorScore(
                        symbol=str(row["symbol"]), data_date=data_date, rank=int(row["rank"]),
                        composite_score=float(row["composite_score"]), factor_values=values,
                    )
                )
            metadata = session.get(WorkspaceSnapshot, "factor_refresh")
            payload = {
                "calculation_scope": "当前 30 只研究候选股；技术因子更新，财务因子沿用最近披露值",
                "updated_factors": sorted(TECHNICAL_FACTORS),
                "stock_count": len(frame),
            }
            if metadata is None:
                metadata = WorkspaceSnapshot(
                    key="factor_refresh", payload=payload, source=f"{history_source} + 最近财务因子",
                    as_of=datetime.combine(data_date, datetime.min.time()), fetched_at=now,
                )
                session.add(metadata)
            else:
                metadata.payload = payload
                metadata.source = f"{history_source} + 最近财务因子"
                metadata.as_of = datetime.combine(data_date, datetime.min.time())
                metadata.fetched_at = now

    def _set_task(self, task_id: str, **values: object) -> None:
        with self.factory.begin() as session:
            task = session.get(ResearchTask, task_id)
            if task is None:
                raise ResourceNotFoundError("未找到因子刷新任务。")
            for name, value in values.items():
                setattr(task, name, value)

    @staticmethod
    def _response(task: ResearchTask) -> FactorRefreshTaskResponse:
        return FactorRefreshTaskResponse(
            task_id=task.id, status=task.status, created_at=task.created_at,
            finished_at=task.finished_at, error_message=task.error_message,
        )
