from dataclasses import dataclass
from datetime import datetime
from threading import Lock
from typing import Protocol
from uuid import uuid4

from fastapi import BackgroundTasks

from app.core.config import get_settings
from app.core.exceptions import ResourceNotFoundError
from app.llm.provider import LLMProvider, build_llm_provider
from app.repositories.research_task_repository import DatabaseTaskStore
from app.schemas.generation import GenerationResultResponse, GenerationTaskResponse
from app.schemas.market import MarketSnapshotResponse
from app.schemas.research import ResearchReportDetail, SourceReference
from app.services.factor_service import FactorService
from app.services.market_data_service import MarketDataService
from app.services.research_service import DISCLAIMER, ResearchService


@dataclass
class StoredTask:
    task_id: str
    symbol: str
    status: str
    created_at: datetime
    finished_at: datetime | None = None
    error_message: str | None = None
    result: ResearchReportDetail | None = None


class TaskStore(Protocol):
    def create(self, symbol: str) -> StoredTask: ...

    def get(self, task_id: str) -> StoredTask: ...

    def mark_running(self, task_id: str) -> None: ...

    def mark_succeeded(self, task_id: str, result: ResearchReportDetail) -> None: ...

    def mark_failed(self, task_id: str, error_message: str) -> None: ...


class InMemoryTaskStore:
    def __init__(self) -> None:
        self._tasks: dict[str, StoredTask] = {}
        self._lock = Lock()

    def create(self, symbol: str) -> StoredTask:
        task = StoredTask(task_id=str(uuid4()), symbol=symbol, status="pending", created_at=datetime.now())
        with self._lock:
            self._tasks[task.task_id] = task
        return task

    def get(self, task_id: str) -> StoredTask:
        with self._lock:
            task = self._tasks.get(task_id)
        if task is None:
            raise ResourceNotFoundError(f"未找到生成任务 {task_id}。")
        return task

    def mark_running(self, task_id: str) -> None:
        self.get(task_id).status = "running"

    def mark_succeeded(self, task_id: str, result: ResearchReportDetail) -> None:
        task = self.get(task_id)
        task.status = "succeeded"
        task.result = result
        task.finished_at = datetime.now()

    def mark_failed(self, task_id: str, error_message: str) -> None:
        task = self.get(task_id)
        task.status = "failed"
        task.error_message = error_message
        task.finished_at = datetime.now()


TASK_STORE = InMemoryTaskStore()


class ResearchGenerationService:
    def __init__(self, *, provider: LLMProvider | None = None, factor_service: FactorService | None = None, research_service: ResearchService | None = None, market_service: MarketDataService | None = None, store: TaskStore | None = None) -> None:
        settings = get_settings()
        self.provider = provider
        self.factor_service = factor_service or FactorService()
        self.research_service = research_service or ResearchService()
        self.market_service = market_service or self._create_market_service(settings)
        self.store = store or self._create_default_store(settings)

    def create_task(self, symbol: str, background_tasks: BackgroundTasks) -> GenerationTaskResponse:
        self.provider = self.provider or build_llm_provider(get_settings())
        item = self._get_factor_item(symbol)
        task = self.store.create(symbol)
        background_tasks.add_task(self._run_task, task.task_id, item)
        return self._to_task_response(task)

    def get_task(self, task_id: str) -> GenerationTaskResponse:
        return self._to_task_response(self.store.get(task_id))

    def get_result(self, task_id: str) -> GenerationResultResponse:
        task = self.store.get(task_id)
        return GenerationResultResponse(**self._to_task_response(task).model_dump(), result=task.result)

    def _run_task(self, task_id: str, item: object) -> None:
        self.store.mark_running(task_id)
        try:
            factor_item = item
            market_snapshot = self._get_market_snapshot(factor_item.symbol)
            prompt = self._build_prompt(factor_item, market_snapshot)
            content = self.provider.generate_markdown(prompt)
            sources = [
                SourceReference(name="AlphaLens 多因子评分快照", type="internal_data"),
                SourceReference(name="OpenAI-compatible LLM generation", type="llm_generated"),
            ]
            if market_snapshot:
                sources.append(SourceReference(name=market_snapshot.source, type="online_market_snapshot", as_of=market_snapshot.as_of.isoformat()))
                sources.extend(
                    SourceReference(name=announcement.source, type="online_disclosure_or_news", as_of=announcement.published_at.isoformat() if announcement.published_at else None)
                    for announcement in market_snapshot.announcements
                )
            result = ResearchReportDetail(
                symbol=factor_item.symbol,
                name=factor_item.name,
                title=f"{factor_item.name}（{factor_item.symbol}）AI 研究更新",
                industry=factor_item.industry,
                generated_at=datetime.now(),
                content_markdown=content,
                sources=_deduplicate_sources(sources),
                disclaimer=DISCLAIMER,
            )
            self.store.mark_succeeded(task_id, result)
        except Exception as error:  # Record provider failures for polling clients.
            self.store.mark_failed(task_id, str(error))

    @staticmethod
    def _create_default_store(settings) -> TaskStore:
        if settings.data_backend == "database":
            if not settings.database_url:
                raise RuntimeError("DATA_BACKEND=database 时必须配置 DATABASE_URL。")
            return DatabaseTaskStore(settings.database_url)
        return TASK_STORE

    @staticmethod
    def _create_market_service(settings) -> MarketDataService | None:
        return MarketDataService(settings=settings) if settings.data_backend == "database" else None

    def _get_market_snapshot(self, symbol: str) -> MarketSnapshotResponse | None:
        if self.market_service is None:
            return None
        try:
            return self.market_service.get_snapshot(symbol)
        except ResourceNotFoundError:
            return None

    def _get_factor_item(self, symbol: str):
        response = self.factor_service.get_top_pool(keyword=symbol, industry=None, limit=1)
        if not response.items or response.items[0].symbol != symbol:
            raise ResourceNotFoundError(f"未找到股票代码 {symbol} 的多因子数据，无法生成报告。")
        return response.items[0]

    @staticmethod
    def _build_prompt(item: object, market_snapshot: MarketSnapshotResponse | None = None) -> str:
        market_context = "未提供在线市场快照。"
        if market_snapshot:
            announcements = "\n".join(
                f"- {announcement.published_at.date().isoformat() if announcement.published_at else '日期未知'}：{announcement.title}（{announcement.source}）"
                for announcement in market_snapshot.announcements[:5]
            ) or "- 当前时间范围没有公告或资讯。"
            market_context = f"""在线市场快照（来源：{market_snapshot.source}；行情时间：{market_snapshot.as_of.isoformat()}；抓取时间：{market_snapshot.fetched_at.isoformat()}）：
- 最新价：{market_snapshot.latest_price}
- 涨跌幅：{market_snapshot.change_percent}
- 成交额：{market_snapshot.amount}
- 主力净流入：{market_snapshot.main_net_inflow}
- 公告与资讯标题：
{announcements}"""
        return f"""请根据下列结构化多因子数据，生成一份中文 Markdown 投研更新。\n\n股票代码：{item.symbol}\n股票名称：{item.name}\n行业：{item.industry}\n多因子排名：{item.rank}\n综合得分：{item.composite_score:.4f}\n因子原始值：{item.factor_values}\n\n{market_context}\n\n要求：\n1. 仅使用给定数据，不编造新闻、财务事实或价格预测。\n2. 若提供在线市场快照，只能陈述其价格、资金流与公告标题，不可从标题推断公告正文或影响。\n3. 包含“因子观察”“市场快照”“风险与限制”“后续跟踪”四个二级标题；无在线市场快照时，在“市场快照”说明数据暂缺。\n4. 明确说明因子数据来自历史课程项目结果，在线快照也可能存在供应商延迟。\n5. 结尾写明“仅供研究学习，不构成投资建议”。"""

    @staticmethod
    def _to_task_response(task: StoredTask) -> GenerationTaskResponse:
        return GenerationTaskResponse(task_id=task.task_id, symbol=task.symbol, status=task.status, created_at=task.created_at, finished_at=task.finished_at, error_message=task.error_message)


def _deduplicate_sources(sources: list[SourceReference]) -> list[SourceReference]:
    deduplicated: list[SourceReference] = []
    seen: set[tuple[str, str, str | None]] = set()
    for source in sources:
        key = (source.name, source.type, source.as_of)
        if key not in seen:
            seen.add(key)
            deduplicated.append(source)
    return deduplicated
