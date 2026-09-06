from datetime import datetime

from pydantic import BaseModel, Field


class MarketAnnouncementItem(BaseModel):
    article_id: str
    title: str
    category: str | None = None
    published_at: datetime | None = None
    url: str | None = None
    source: str


class MarketSnapshotResponse(BaseModel):
    symbol: str = Field(pattern=r"^\d{6}$")
    name: str
    latest_price: float
    change_amount: float | None = None
    change_percent: float | None = None
    open_price: float | None = None
    high_price: float | None = None
    low_price: float | None = None
    volume: float | None = None
    amount: float | None = None
    total_market_cap: float | None = None
    main_net_inflow: float | None = None
    source: str
    as_of: datetime
    fetched_at: datetime
    freshness: str
    warning: str | None = None
    announcements: list[MarketAnnouncementItem]
