from datetime import datetime
from pathlib import Path

from app.core.config import Settings
from app.core.exceptions import MarketDataProviderError
from app.db.base import Base
from app.db.models import Stock
from app.db.session import get_engine, get_session_factory
from app.market.eastmoney_provider import FetchedAnnouncement, FetchedQuote
from app.services.market_data_service import MarketDataService


class StaticMarketProvider:
    def fetch_quote(self, symbol: str) -> FetchedQuote:
        return FetchedQuote(
            symbol=symbol,
            name="巨人网络",
            latest_price=29.56,
            change_amount=1.24,
            change_percent=4.38,
            open_price=27.9,
            high_price=29.88,
            low_price=27.4,
            volume=1455411,
            amount=4206352829.94,
            total_market_cap=56180611862.76,
            main_net_inflow=-2132496,
            as_of=datetime(2026, 7, 11, 10, 30),
        )

    def fetch_announcements(self, _: str, __: int) -> list[FetchedAnnouncement]:
        return [
            FetchedAnnouncement(
                article_id="AN202607071826775766",
                title="巨人网络:2026年半年度业绩预告",
                category="业绩预告",
                published_at=datetime(2026, 7, 8),
                url="https://example.com/announcement",
            )
        ]


class FailingMarketProvider:
    def fetch_quote(self, _: str) -> FetchedQuote:
        raise MarketDataProviderError("上游服务暂不可用")

    def fetch_announcements(self, _: str, __: int) -> list[FetchedAnnouncement]:
        raise MarketDataProviderError("上游服务暂不可用")


def test_market_refresh_persists_quote_and_announcements(tmp_path: Path) -> None:
    database_url = f"sqlite:///{tmp_path / 'market.db'}"
    Base.metadata.create_all(get_engine(database_url))
    with get_session_factory(database_url).begin() as session:
        session.add(Stock(symbol="002558", name="巨人网络", industry="传媒"))

    settings = Settings(database_url=database_url)
    refreshed = MarketDataService(settings=settings, provider=StaticMarketProvider()).refresh_stock("002558")
    cached = MarketDataService(settings=settings, provider=StaticMarketProvider()).get_snapshot("002558")

    assert refreshed.freshness == "fresh"
    assert refreshed.latest_price == 29.56
    assert refreshed.announcements[0].article_id == "AN202607071826775766"
    assert cached.freshness == "cached"
    assert cached.change_percent == 4.38


def test_market_refresh_returns_stale_snapshot_when_provider_fails(tmp_path: Path) -> None:
    database_url = f"sqlite:///{tmp_path / 'market.db'}"
    Base.metadata.create_all(get_engine(database_url))
    with get_session_factory(database_url).begin() as session:
        session.add(Stock(symbol="002558", name="巨人网络", industry="传媒"))

    settings = Settings(database_url=database_url)
    MarketDataService(settings=settings, provider=StaticMarketProvider()).refresh_stock("002558")
    stale = MarketDataService(settings=settings, provider=FailingMarketProvider()).refresh_stock("002558")

    assert stale.freshness == "stale"
    assert stale.warning is not None
