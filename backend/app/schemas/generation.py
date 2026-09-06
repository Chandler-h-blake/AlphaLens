from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from app.schemas.research import ResearchReportDetail


TaskStatus = Literal["pending", "running", "succeeded", "failed"]


class GenerationTaskResponse(BaseModel):
    task_id: str
    symbol: str
    status: TaskStatus
    created_at: datetime
    finished_at: datetime | None = None
    error_message: str | None = None


class GenerationResultResponse(GenerationTaskResponse):
    result: ResearchReportDetail | None = None
