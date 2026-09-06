from typing import Annotated

from fastapi import APIRouter, Depends

from app.schemas.industry import IndustryDatesResponse, IndustryRotationResponse
from app.services.industry_service import IndustryService


router = APIRouter()


def get_industry_service() -> IndustryService:
    return IndustryService()


IndustryServiceDependency = Annotated[IndustryService, Depends(get_industry_service)]


@router.post('/rotation/refresh', response_model=IndustryRotationResponse)
def refresh(service: IndustryServiceDependency):
    from app.services.industry_refresh import refresh_rotation
    try:
        refresh_rotation()
        return service.get_rotation()
    except Exception:
        return service.get_rotation().model_copy(update={'warning': '行业刷新失败，继续展示已保存的历史快照。'})


@router.get("/rotation", response_model=IndustryRotationResponse, summary="查询行业轮动结果")
def get_rotation(service: IndustryServiceDependency) -> IndustryRotationResponse:
    return service.get_rotation()


@router.get("/rotation/dates", response_model=IndustryDatesResponse, summary="查询可用行业轮动日期")
def get_dates(service: IndustryServiceDependency) -> IndustryDatesResponse:
    return service.get_dates()
