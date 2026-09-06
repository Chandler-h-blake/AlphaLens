from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Query

from app.schemas.factors import FactorOverviewResponse, FactorRefreshTaskResponse, FactorTopPoolResponse
from app.services.factor_refresh_service import FactorRefreshService
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


@router.post("/refresh", response_model=FactorRefreshTaskResponse, summary="创建候选池技术因子刷新任务")
def refresh_factors(background_tasks: BackgroundTasks) -> FactorRefreshTaskResponse:
    return FactorRefreshService().create(background_tasks)


@router.get("/refresh/tasks/{task_id}", response_model=FactorRefreshTaskResponse, summary="查询因子刷新任务")
def get_refresh_task(task_id: str) -> FactorRefreshTaskResponse:
    return FactorRefreshService().get(task_id)
