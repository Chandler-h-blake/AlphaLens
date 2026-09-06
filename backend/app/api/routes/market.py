from typing import Annotated

from fastapi import APIRouter, Depends, Path

from app.schemas.market import MarketSnapshotResponse
from app.services.market_data_service import MarketDataService


router = APIRouter()


def get_market_data_service() -> MarketDataService:
    return MarketDataService()


MarketDataServiceDependency = Annotated[MarketDataService, Depends(get_market_data_service)]


@router.get("/stocks/{symbol}", response_model=MarketSnapshotResponse, summary="读取已缓存的在线行情快照")
def get_stock_snapshot(
    service: MarketDataServiceDependency,
    symbol: str = Path(pattern=r"^\d{6}$"),
) -> MarketSnapshotResponse:
    return service.get_snapshot(symbol)


@router.post("/stocks/{symbol}/refresh", response_model=MarketSnapshotResponse, summary="联网刷新股票行情与公司公告")
def refresh_stock_snapshot(
    service: MarketDataServiceDependency,
    symbol: str = Path(pattern=r"^\d{6}$"),
) -> MarketSnapshotResponse:
    return service.refresh_stock(symbol)
