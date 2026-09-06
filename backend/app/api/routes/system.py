from datetime import datetime

from fastapi import APIRouter
from sqlalchemy import select

from app.core.config import get_settings
from app.db.models import WorkspaceSnapshot
from app.db.session import get_session_factory
from app.schemas.dashboard import SystemStatusResponse

router = APIRouter()


@router.get("/status", response_model=SystemStatusResponse)
def get_status() -> SystemStatusResponse:
    settings = get_settings()
    snapshots: dict[str, datetime | None] = {"dashboard": None, "funds": None}
    ready = bool(settings.database_url)
    if settings.database_url:
        with get_session_factory(settings.database_url)() as session:
            for item in session.scalars(select(WorkspaceSnapshot)).all():
                snapshots[item.key] = item.fetched_at
    return SystemStatusResponse(app_name=settings.app_name, database_ready=ready, llm_configured=bool(settings.llm_api_key) and settings.llm_provider == "openai_compatible", market_provider=settings.market_data_provider, snapshots=snapshots)
