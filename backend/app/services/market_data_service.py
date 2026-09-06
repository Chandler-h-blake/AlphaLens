from datetime import datetime, timedelta

from app.core.config import Settings, get_settings
from app.core.exceptions import MarketDataProviderError, ResourceNotFoundError
from app.db.models import MarketAnnouncement, MarketSnapshot
from app.market.eastmoney_provider import MarketDataProvider, build_market_data_provider
from app.repositories.market_repository import MarketRepository
from app.schemas.market import MarketAnnouncementItem, MarketSnapshotResponse


class MarketDataService:
    def __init__(self, *, settings: Settings | None = None, provider: MarketDataProvider | None = None, repository: MarketRepository | None = None) -> None:
        self.settings = settings or get_settings()
        if not self.settings.database_url:
            raise MarketDataProviderError("在线行情功能需要配置 DATABASE_URL。")
        self.provider = provider or build_market_data_provider(self.settings)
        self.repository = repository or MarketRepository(self.settings.database_url)

    def get_snapshot(self, symbol: str) -> MarketSnapshotResponse:
        snapshot, announcements = self.repository.get_snapshot(symbol)
        return self._to_response(snapshot, announcements, freshness="cached")

    def refresh_stock(self, symbol: str) -> MarketSnapshotResponse:
        try:
            quote = self.provider.fetch_quote(symbol)
            announcements = self.provider.fetch_announcements(symbol, self.settings.market_announcement_limit)
            snapshot, persisted_announcements = self.repository.save_refresh(quote, announcements)
            return self._to_response(snapshot, persisted_announcements, freshness="fresh")
        except MarketDataProviderError as error:
            try:
                snapshot, announcements = self.repository.get_snapshot(symbol)
            except ResourceNotFoundError:
                raise error
            return self._to_response(
                snapshot,
                announcements,
                freshness="stale",
                warning=f"在线数据更新失败，正在展示最近一次成功快照：{error}",
            )

    @staticmethod
    def _to_response(snapshot: MarketSnapshot, announcements: list[MarketAnnouncement], *, freshness: str, warning: str | None = None) -> MarketSnapshotResponse:
        if freshness == "cached" and datetime.now() - snapshot.fetched_at > timedelta(minutes=15):
            freshness = "stale"
            warning = "当前展示的是超过 15 分钟的历史快照，请刷新在线数据。"
        return MarketSnapshotResponse(
            symbol=snapshot.symbol,
            name=snapshot.name,
            latest_price=snapshot.latest_price,
            change_amount=snapshot.change_amount,
            change_percent=snapshot.change_percent,
            open_price=snapshot.open_price,
            high_price=snapshot.high_price,
            low_price=snapshot.low_price,
            volume=snapshot.volume,
            amount=snapshot.amount,
            total_market_cap=snapshot.total_market_cap,
            main_net_inflow=snapshot.main_net_inflow,
            source=snapshot.source,
            as_of=snapshot.as_of,
            fetched_at=snapshot.fetched_at,
            freshness=freshness,
            warning=warning,
            announcements=[
                MarketAnnouncementItem(
                    article_id=item.article_id,
                    title=item.title,
                    category=item.category,
                    published_at=item.published_at,
                    url=item.url,
                    source=item.source,
                )
                for item in announcements
            ],
        )
