import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.api.router import api_router
from app.api.routes.public import router as public_router
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.observability import PublicWriteRateLimitMiddleware, RequestContextMiddleware
from app.repositories.research_task_repository import DatabaseTaskStore


settings = get_settings()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.task_recovery_enabled and settings.data_backend == "database" and settings.database_url:
        recovered_count = DatabaseTaskStore(settings.database_url).mark_interrupted_tasks()
        if recovered_count:
            logger.warning("Marked %s interrupted research task(s) as failed after startup.", recovered_count)
    yield

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="为 AlphaLens 前端提供市场快照、因子选股、行业轮动和 AI 研究任务接口。",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)
app.add_middleware(
    PublicWriteRateLimitMiddleware,
    enabled=settings.public_write_rate_limit_enabled,
    market_refresh_limit_per_minute=settings.market_refresh_limit_per_minute,
    report_generation_limit_per_hour=settings.report_generation_limit_per_hour,
    factor_refresh_limit_per_hour=settings.factor_refresh_limit_per_hour,
)
# Middleware added last is outermost in Starlette, so it also decorates early 429 responses.
app.add_middleware(RequestContextMiddleware)

register_exception_handlers(app)
app.include_router(api_router, prefix=settings.api_prefix)
app.include_router(public_router)


frontend_dist = settings.frontend_dist_path
if frontend_dist.is_dir():
    index_file = frontend_dist / "index.html"

    @app.get("/{requested_path:path}", include_in_schema=False)
    def serve_frontend(requested_path: str):
        """Serve built React assets and let client-side routing handle application paths."""
        candidate = (frontend_dist / requested_path).resolve()
        try:
            candidate.relative_to(frontend_dist.resolve())
        except ValueError:
            return FileResponse(index_file)
        if candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(index_file)
