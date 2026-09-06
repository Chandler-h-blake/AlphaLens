from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from fastapi import BackgroundTasks
from sqlalchemy import select

from app.core.config import Settings, get_settings
from app.core.exceptions import LLMConfigurationError, ResourceNotFoundError
from app.db.models import DailyReview, ResearchTask, WorkspaceSnapshot
from app.repositories.research_task_repository import DatabaseTaskStore
from app.db.session import get_session_factory
from app.llm.provider import build_llm_provider
from app.schemas.dashboard import ReviewResultResponse, ReviewTaskResponse


class ReviewService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        if not self.settings.database_url:
            raise RuntimeError("每日复盘需要配置 DATABASE_URL。")
        self.factory = get_session_factory(self.settings.database_url)
        self.store = DatabaseTaskStore(self.settings.database_url)

    def create(self, background_tasks: BackgroundTasks) -> ReviewTaskResponse:
        if self.settings.llm_provider != "openai_compatible" or not self.settings.llm_api_key:
            raise LLMConfigurationError("未配置 LLM_API_KEY，无法生成 AI 每日复盘。")
        task = ResearchTask(id=str(uuid4()), symbol="", kind="daily_review", status="pending", created_at=datetime.now())
        with self.factory.begin() as session:
            session.add(task)
        background_tasks.add_task(self._run, task.id)
        return self._response(task)

    def get(self, task_id: str) -> ReviewTaskResponse:
        with self.factory() as session:
            task = session.get(ResearchTask, task_id)
            if task is None or task.kind != "daily_review":
                raise ResourceNotFoundError("未找到每日复盘任务。")
            return self._response(task)

    def result(self, task_id: str) -> ReviewResultResponse:
        with self.factory() as session:
            task = session.get(ResearchTask, task_id)
            if task is None or task.kind != "daily_review":
                raise ResourceNotFoundError("未找到每日复盘任务。")
            content = session.get(DailyReview, task.review_id).content_markdown if task.review_id else None
            return ReviewResultResponse(**self._response(task).model_dump(), content_markdown=content)

    def _run(self, task_id: str) -> None:
        with self.factory.begin() as session:
            task = session.get(ResearchTask, task_id)
            task.status = "running"
            dashboard = session.scalar(select(WorkspaceSnapshot).where(WorkspaceSnapshot.key == "dashboard"))
            funds = session.scalar(select(WorkspaceSnapshot).where(WorkspaceSnapshot.key == "funds"))
        try:
            prompt = f"""根据以下 A 股结构化快照生成中文每日复盘。只陈述提供的数据，不编造新闻、政策、预测或交易指令。必须包含：市场概览、资金观察、风险与限制、后续跟踪。结尾写‘仅供研究学习，不构成投资建议’。\n市场快照：{dashboard.payload if dashboard else {}}\n资金快照：{funds.payload if funds else {}}"""
            content = build_llm_provider(self.settings).generate_markdown(prompt)
            with self.factory.begin() as session:
                review = DailyReview(content_markdown=content, generated_at=datetime.now(), source_summary={"dashboard": bool(dashboard), "funds": bool(funds)})
                session.add(review)
                session.flush()
                task = session.get(ResearchTask, task_id)
                task.status, task.review_id, task.finished_at = "succeeded", review.id, datetime.now()
        except Exception as error:
            self.store.mark_failed(task_id, str(error))

    @staticmethod
    def _response(task: ResearchTask) -> ReviewTaskResponse:
        return ReviewTaskResponse(task_id=task.id, status=task.status, created_at=task.created_at, finished_at=task.finished_at, error_message=task.error_message)
