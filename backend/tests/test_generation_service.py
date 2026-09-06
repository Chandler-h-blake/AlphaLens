import asyncio
from pathlib import Path

from fastapi import BackgroundTasks

from app.db.base import Base
from app.db.models import Stock
from app.db.session import get_engine, get_session_factory
from app.repositories.research_task_repository import DatabaseTaskStore
from app.schemas.factors import FactorTopPoolItem, FactorTopPoolResponse
from app.services.research_generation_service import InMemoryTaskStore, ResearchGenerationService


class StaticProvider:
    def generate_markdown(self, _: str) -> str:
        return "## 因子观察\n测试生成内容。\n\n## 风险与限制\n仅有因子数据。\n\n## 后续跟踪\n关注数据更新。\n\n仅供研究学习，不构成投资建议。"


class StaticFactorService:
    def get_top_pool(self, **_: object) -> FactorTopPoolResponse:
        return FactorTopPoolResponse(source="test", total=1, items=[FactorTopPoolItem(symbol="002558", name="巨人网络", industry="传媒", rank=1, composite_score=1.95, factor_values={"roe": 6.81})])


def test_generation_task_completes_with_injected_provider() -> None:
    service = ResearchGenerationService(provider=StaticProvider(), factor_service=StaticFactorService(), store=InMemoryTaskStore())
    background_tasks = BackgroundTasks()

    created = service.create_task("002558", background_tasks)
    asyncio.run(background_tasks())
    result = service.get_result(created.task_id)

    assert result.status == "succeeded"
    assert result.result is not None
    assert result.result.symbol == "002558"
    assert "因子观察" in result.result.content_markdown


def test_generation_task_and_report_survive_a_new_database_store(tmp_path: Path) -> None:
    database_url = f"sqlite:///{tmp_path / 'research.db'}"
    Base.metadata.create_all(get_engine(database_url))
    with get_session_factory(database_url).begin() as session:
        session.add(Stock(symbol="002558", name="巨人网络", industry="传媒"))

    service = ResearchGenerationService(
        provider=StaticProvider(),
        factor_service=StaticFactorService(),
        store=DatabaseTaskStore(database_url),
    )
    background_tasks = BackgroundTasks()
    created = service.create_task("002558", background_tasks)
    asyncio.run(background_tasks())

    recovered = DatabaseTaskStore(database_url).get(created.task_id)

    assert recovered.status == "succeeded"
    assert recovered.result is not None
    assert recovered.result.title == "巨人网络（002558）AI 研究更新"


def test_database_store_marks_interrupted_tasks_as_failed(tmp_path: Path) -> None:
    database_url = f"sqlite:///{tmp_path / 'research.db'}"
    Base.metadata.create_all(get_engine(database_url))
    store = DatabaseTaskStore(database_url)
    task = store.create("002558")
    store.mark_running(task.task_id)

    recovered_count = DatabaseTaskStore(database_url).mark_interrupted_tasks()
    recovered = DatabaseTaskStore(database_url).get(task.task_id)

    assert recovered_count == 1
    assert recovered.status == "failed"
    assert recovered.finished_at is not None
    assert recovered.error_message == "服务重启导致任务中断，请重新生成。"
