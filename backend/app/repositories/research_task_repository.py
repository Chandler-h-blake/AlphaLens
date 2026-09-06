from datetime import datetime
from uuid import uuid4

from sqlalchemy import update

from app.core.exceptions import ResourceNotFoundError
from app.db.models import ResearchReport, ResearchTask
from app.db.session import get_session_factory
from app.schemas.research import ResearchReportDetail, SourceReference
from app.services.research_service import DISCLAIMER


class DatabaseTaskStore:
    """Persist generation task state and completed reports in the application database."""

    def __init__(self, database_url: str) -> None:
        self.session_factory = get_session_factory(database_url)

    def create(self, symbol: str):
        from app.services.research_generation_service import StoredTask

        task = StoredTask(task_id=str(uuid4()), symbol=symbol, status="pending", created_at=datetime.now())
        with self.session_factory.begin() as session:
            session.add(
                ResearchTask(
                    id=task.task_id,
                    symbol=task.symbol,
                    status=task.status,
                    created_at=task.created_at,
                )
            )
        return task

    def get(self, task_id: str):
        from app.services.research_generation_service import StoredTask

        with self.session_factory() as session:
            task = session.get(ResearchTask, task_id)
            if task is None:
                raise ResourceNotFoundError(f"未找到生成任务 {task_id}。")
            result = self._load_result(session, task.report_id)
            return StoredTask(
                task_id=task.id,
                symbol=task.symbol,
                status=task.status,
                created_at=task.created_at,
                finished_at=task.finished_at,
                error_message=task.error_message,
                result=result,
            )

    def mark_running(self, task_id: str) -> None:
        self._update_task(task_id, status="running")

    def mark_succeeded(self, task_id: str, result: ResearchReportDetail) -> None:
        with self.session_factory.begin() as session:
            task = self._require_task(session, task_id)
            report = ResearchReport(
                symbol=result.symbol,
                name=result.name,
                title=result.title,
                industry=result.industry,
                generated_at=result.generated_at,
                content_markdown=result.content_markdown,
                sources=[source.model_dump() for source in result.sources],
                source_file=f"task:{task_id}",
            )
            session.add(report)
            session.flush()
            task.status = "succeeded"
            task.finished_at = datetime.now()
            task.error_message = None
            task.report_id = report.id

    def mark_failed(self, task_id: str, error_message: str) -> None:
        self._update_task(task_id, status="failed", error_message=error_message, finished_at=datetime.now())

    def mark_interrupted_tasks(self) -> int:
        """Prevent polling clients from waiting forever after a process restart."""
        with self.session_factory.begin() as session:
            result = session.execute(
                update(ResearchTask)
                .where(ResearchTask.status.in_(["pending", "running"]))
                .values(
                    status="failed",
                    error_message="服务重启导致任务中断，请重新生成。",
                    finished_at=datetime.now(),
                )
            )
            return result.rowcount or 0

    def _update_task(self, task_id: str, **values: object) -> None:
        with self.session_factory.begin() as session:
            task = self._require_task(session, task_id)
            for name, value in values.items():
                setattr(task, name, value)

    @staticmethod
    def _require_task(session, task_id: str) -> ResearchTask:
        task = session.get(ResearchTask, task_id)
        if task is None:
            raise ResourceNotFoundError(f"未找到生成任务 {task_id}。")
        return task

    @staticmethod
    def _load_result(session, report_id: int | None) -> ResearchReportDetail | None:
        if report_id is None:
            return None
        report = session.get(ResearchReport, report_id)
        if report is None:
            return None
        return ResearchReportDetail(
            symbol=report.symbol,
            name=report.name,
            title=report.title,
            industry=report.industry,
            generated_at=report.generated_at,
            content_markdown=report.content_markdown,
            sources=[SourceReference.model_validate(source) for source in report.sources],
            disclaimer=DISCLAIMER,
        )
