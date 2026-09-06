from datetime import datetime

from pydantic import BaseModel


class SourceReference(BaseModel):
    name: str
    type: str
    as_of: str | None = None


class ResearchReportListItem(BaseModel):
    symbol: str
    name: str
    title: str
    industry: str | None = None
    generated_at: datetime | None = None


class ResearchReportListResponse(BaseModel):
    source: str
    items: list[ResearchReportListItem]
    total: int


class ResearchReportDetail(ResearchReportListItem):
    content_markdown: str
    sources: list[SourceReference]
    disclaimer: str

