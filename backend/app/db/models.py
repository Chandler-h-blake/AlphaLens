from datetime import UTC, date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def utc_now() -> datetime:
    """Return naive UTC for database columns that intentionally omit timezone metadata."""
    return datetime.now(UTC).replace(tzinfo=None)


class Stock(Base):
    __tablename__ = "stocks"

    symbol: Mapped[str] = mapped_column(String(6), primary_key=True)
    name: Mapped[str] = mapped_column(String(64))
    industry: Mapped[str | None] = mapped_column(String(64), nullable=True)


class FactorScore(Base):
    __tablename__ = "factor_scores"
    __table_args__ = (UniqueConstraint("symbol", "data_date", name="uq_factor_score_symbol_date"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    symbol: Mapped[str] = mapped_column(ForeignKey("stocks.symbol"), index=True)
    data_date: Mapped[date] = mapped_column(Date, index=True)
    rank: Mapped[int] = mapped_column(Integer, index=True)
    composite_score: Mapped[float] = mapped_column(Float)
    factor_values: Mapped[dict[str, float | None]] = mapped_column(JSON)


class FactorOverview(Base):
    __tablename__ = "factor_overviews"
    __table_args__ = (UniqueConstraint("factor", "data_date", name="uq_factor_overview_factor_date"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    factor: Mapped[str] = mapped_column(String(64), index=True)
    data_date: Mapped[date] = mapped_column(Date, index=True)
    name: Mapped[str] = mapped_column(String(64))
    category: Mapped[str] = mapped_column(String(32))
    direction: Mapped[int] = mapped_column(Integer)
    direction_text: Mapped[str] = mapped_column(String(32))
    weight: Mapped[float] = mapped_column(Float)
    data_source: Mapped[str] = mapped_column(String(128))
    description: Mapped[str] = mapped_column(Text)
    metrics: Mapped[dict[str, float | int | None]] = mapped_column(JSON)


class ResearchReport(Base):
    __tablename__ = "research_reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    symbol: Mapped[str] = mapped_column(ForeignKey("stocks.symbol"), index=True)
    name: Mapped[str] = mapped_column(String(64))
    title: Mapped[str] = mapped_column(String(256))
    industry: Mapped[str | None] = mapped_column(String(64), nullable=True)
    generated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    content_markdown: Mapped[str] = mapped_column(Text)
    sources: Mapped[list[dict[str, str | None]]] = mapped_column(JSON)
    source_file: Mapped[str | None] = mapped_column(String(256), nullable=True)


class IndustryRotation(Base):
    __tablename__ = "industry_rotations"
    __table_args__ = (UniqueConstraint("industry_code", "data_date", name="uq_industry_rotation_code_date"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    industry_code: Mapped[str] = mapped_column(String(32), index=True)
    data_date: Mapped[date] = mapped_column(Date, index=True)
    industry_name: Mapped[str] = mapped_column(String(64))
    latest_close: Mapped[float | None] = mapped_column(Float, nullable=True)
    return_1m: Mapped[float] = mapped_column(Float)
    return_3m: Mapped[float] = mapped_column(Float)
    rank_1m: Mapped[int] = mapped_column(Integer)
    rank_3m: Mapped[int] = mapped_column(Integer)
    rotation_type: Mapped[str] = mapped_column(String(32))
    generated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class ResearchTask(Base):
    __tablename__ = "research_tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    symbol: Mapped[str] = mapped_column(String(6), index=True)
    status: Mapped[str] = mapped_column(String(16), index=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    report_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    kind: Mapped[str] = mapped_column(String(32), default="research_report")
    review_id: Mapped[int | None] = mapped_column(Integer, nullable=True)


class SourceDocument(Base):
    __tablename__ = "source_documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_type: Mapped[str] = mapped_column(String(64))
    title: Mapped[str] = mapped_column(String(256))
    content: Mapped[str] = mapped_column(Text)
    as_of: Mapped[date | None] = mapped_column(Date, nullable=True)


class MarketSnapshot(Base):
    __tablename__ = "market_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True)
    symbol: Mapped[str] = mapped_column(ForeignKey("stocks.symbol"), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(64))
    latest_price: Mapped[float] = mapped_column(Float)
    change_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    change_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    open_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    high_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    low_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    volume: Mapped[float | None] = mapped_column(Float, nullable=True)
    amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_market_cap: Mapped[float | None] = mapped_column(Float, nullable=True)
    main_net_inflow: Mapped[float | None] = mapped_column(Float, nullable=True)
    source: Mapped[str] = mapped_column(String(128))
    as_of: Mapped[datetime] = mapped_column(DateTime, index=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, index=True)


class MarketAnnouncement(Base):
    __tablename__ = "market_announcements"
    __table_args__ = (UniqueConstraint("symbol", "article_id", name="uq_market_announcement_symbol_article"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    symbol: Mapped[str] = mapped_column(ForeignKey("stocks.symbol"), index=True)
    article_id: Mapped[str] = mapped_column(String(64))
    title: Mapped[str] = mapped_column(String(512))
    category: Mapped[str | None] = mapped_column(String(128), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    source: Mapped[str] = mapped_column(String(128))
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class WorkspaceSnapshot(Base):
    __tablename__ = "workspace_snapshots"

    key: Mapped[str] = mapped_column(String(32), primary_key=True)
    payload: Mapped[dict] = mapped_column(JSON)
    source: Mapped[str] = mapped_column(String(128))
    as_of: Mapped[datetime] = mapped_column(DateTime, index=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, index=True)


class DailyReview(Base):
    __tablename__ = "daily_reviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    content_markdown: Mapped[str] = mapped_column(Text)
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, index=True)
    source_summary: Mapped[dict] = mapped_column(JSON)
