from fastapi import APIRouter
from sqlalchemy import text

from app.core.config import get_settings
from app.core.exceptions import DataSourceError
from app.db.session import get_session_factory
from app.schemas.health import HealthResponse, ReadinessResponse


router = APIRouter()


@router.get("/health", response_model=HealthResponse, summary="检查 API 服务状态")
@router.head("/health", include_in_schema=False)
def get_health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(status="ok", environment=settings.app_env)


@router.get("/health/live", response_model=HealthResponse, summary="检查 API 进程是否存活")
@router.head("/health/live", include_in_schema=False)
def get_liveness() -> HealthResponse:
    return get_health()


@router.get("/health/ready", response_model=ReadinessResponse, summary="检查 API 与数据库是否就绪")
@router.head("/health/ready", include_in_schema=False)
def get_readiness() -> ReadinessResponse:
    settings = get_settings()
    if settings.data_backend != "database":
        return ReadinessResponse(status="ok", environment=settings.app_env, database="not_required")
    if not settings.database_url:
        raise DataSourceError("DATA_BACKEND=database 时未配置 DATABASE_URL。")
    try:
        with get_session_factory(settings.database_url)() as session:
            session.execute(text("SELECT 1"))
    except Exception as error:
        raise DataSourceError(f"数据库尚未就绪：{error}") from error
    return ReadinessResponse(status="ok", environment=settings.app_env, database="ok")
