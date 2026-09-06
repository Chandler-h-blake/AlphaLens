from pydantic import BaseModel


class IndustryRotationItem(BaseModel):
    industry_code: str
    industry_name: str
    last_date: str
    latest_close: float | None = None
    return_1m: float
    return_3m: float
    rank_1m: int
    rank_3m: int
    rotation_type: str
    generated_at: str


class IndustryRotationResponse(BaseModel):
    warning: str | None = None
    source: str
    data_date: str
    items: list[IndustryRotationItem]
    total: int


class IndustryDatesResponse(BaseModel):
    items: list[str]
