from datetime import datetime

from sqlalchemy import select

from app.core.exceptions import ResourceNotFoundError
from app.db.models import MarketAnnouncement, MarketSnapshot, Stock
from app.db.session import get_session_factory
from app.market.eastmoney_provider import FetchedAnnouncement, FetchedQuote


class MarketRepository:
    """Store online provider results so the UI stays usable when a provider is temporarily unavailable."""

    def __init__(self, database_url: str) -> None:
        self.session_factory = get_session_factory(database_url)

    def get_snapshot(self, symbol: str) -> tuple[MarketSnapshot, list[MarketAnnouncement]]:
        with self.session_factory() as session:
            snapshot = session.scalar(select(MarketSnapshot).where(MarketSnapshot.symbol == symbol))
            if snapshot is None:
                raise ResourceNotFoundError(f"股票代码 {symbol} 暂无在线行情快照，请先刷新。")
            announcements = session.scalars(
                select(MarketAnnouncement)
                .where(MarketAnnouncement.symbol == symbol)
                .order_by(MarketAnnouncement.published_at.desc().nullslast(), MarketAnnouncement.id.desc())
            ).all()
            return snapshot, announcements

    def save_refresh(self, quote: FetchedQuote, announcements: list[FetchedAnnouncement]) -> tuple[MarketSnapshot, list[MarketAnnouncement]]:
        with self.session_factory.begin() as session:
            stock = session.get(Stock, quote.symbol)
            if stock is None:
                raise ResourceNotFoundError(f"股票代码 {quote.symbol} 不在当前研究股票池中。")
            snapshot = session.scalar(select(MarketSnapshot).where(MarketSnapshot.symbol == quote.symbol))
            if snapshot is None:
                snapshot = MarketSnapshot(symbol=quote.symbol, name=quote.name, latest_price=quote.latest_price, source=quote.source, as_of=quote.as_of, fetched_at=datetime.now())
                session.add(snapshot)
            snapshot.name = quote.name
            snapshot.latest_price = quote.latest_price
            snapshot.change_amount = quote.change_amount
            snapshot.change_percent = quote.change_percent
            snapshot.open_price = quote.open_price
            snapshot.high_price = quote.high_price
            snapshot.low_price = quote.low_price
            snapshot.volume = quote.volume
            snapshot.amount = quote.amount
            snapshot.total_market_cap = quote.total_market_cap
            snapshot.main_net_inflow = quote.main_net_inflow
            snapshot.source = quote.source
            snapshot.as_of = quote.as_of
            snapshot.fetched_at = datetime.now()

            existing = {
                item.article_id: item
                for item in session.scalars(select(MarketAnnouncement).where(MarketAnnouncement.symbol == quote.symbol)).all()
            }
            for record in announcements:
                announcement = existing.get(record.article_id)
                if announcement is None:
                    announcement = MarketAnnouncement(symbol=quote.symbol, article_id=record.article_id, title=record.title, source=record.source, fetched_at=datetime.now())
                    session.add(announcement)
                announcement.title = record.title
                announcement.category = record.category
                announcement.published_at = record.published_at
                announcement.url = record.url
                announcement.source = record.source
                announcement.fetched_at = datetime.now()
            session.flush()
            persisted_announcements = session.scalars(
                select(MarketAnnouncement)
                .where(MarketAnnouncement.symbol == quote.symbol)
                .order_by(MarketAnnouncement.published_at.desc().nullslast(), MarketAnnouncement.id.desc())
            ).all()
            return snapshot, persisted_announcements
