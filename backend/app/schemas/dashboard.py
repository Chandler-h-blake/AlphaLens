from datetime import datetime
from typing import Any

from pydantic import BaseModel


class SnapshotResponse(BaseModel):
    data: dict[str, Any]
    source: str
    as_of: datetime
    fetched_at: datetime
    freshness: str
    warning: str | None = None


class SystemStatusResponse(BaseModel):
    app_name: str
    database_ready: bool
    llm_configured: bool
    market_provider: str
    snapshots: dict[str, datetime | None]


class ReviewTaskResponse(BaseModel):
    task_id: str
    status: str
    created_at: datetime
    finished_at: datetime | None = None
    error_message: str | None = None


class ReviewResultResponse(ReviewTaskResponse):
    content_markdown: str | None = None
