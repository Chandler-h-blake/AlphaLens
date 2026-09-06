from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


class FactorTopPoolItem(BaseModel):
    symbol: str = Field(description="六位股票代码")
    name: str
    industry: str
    rank: int = Field(ge=1)
    composite_score: float
    factor_values: dict[str, float | None]


class FactorTopPoolResponse(BaseModel):
    source: str
    data_date: date | None = None
    refreshed_at: datetime | None = None
    calculation_scope: str = "已保存的研究候选池"
    items: list[FactorTopPoolItem]
    total: int = Field(ge=0)


class FactorRefreshTaskResponse(BaseModel):
    task_id: str
    status: Literal["pending", "running", "succeeded", "failed"]
    created_at: datetime
    finished_at: datetime | None = None
    error_message: str | None = None


class FactorOverviewItem(BaseModel):
    factor: str
    name: str
    category: str
    direction: int
    direction_text: str
    weight: float
    data_source: str
    description: str
    spearman_ic_adjusted: float | None = None
    pearson_ic_adjusted: float | None = None
    ic_positive_rate: float | None = None
    group1_minus_group5: float | None = None
    group_spread_positive_rate: float | None = None
    validation_n: float | None = None
    snapshot_count: int | None = None


class FactorOverviewResponse(BaseModel):
    source: str
    items: list[FactorOverviewItem]
    total: int = Field(ge=0)
