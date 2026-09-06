from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.schemas.factors import FactorOverviewResponse, FactorTopPoolResponse
from app.services.factor_service import FactorService


router = APIRouter()


def get_factor_service() -> FactorService:
    return FactorService()


FactorServiceDependency = Annotated[FactorService, Depends(get_factor_service)]


@router.get("/top30", response_model=FactorTopPoolResponse, summary="查询多因子 TOP30 股票池")
def get_top30(
    service: FactorServiceDependency,
    keyword: str | None = Query(default=None, min_length=1, max_length=50),
    industry: str | None = Query(default=None, min_length=1, max_length=50),
    limit: int = Query(default=30, ge=1, le=100),
) -> FactorTopPoolResponse:
    return service.get_top_pool(keyword=keyword, industry=industry, limit=limit)


@router.get("/overview", response_model=FactorOverviewResponse, summary="查询因子有效性概览")
def get_overview(service: FactorServiceDependency) -> FactorOverviewResponse:
    return service.get_overview()

