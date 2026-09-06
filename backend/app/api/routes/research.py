from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Path

from app.schemas.generation import GenerationResultResponse, GenerationTaskResponse
from app.schemas.research import ResearchReportDetail, ResearchReportListResponse
from app.services.research_generation_service import ResearchGenerationService
from app.services.research_service import ResearchService


router = APIRouter()


def get_research_service() -> ResearchService:
    return ResearchService()


ResearchServiceDependency = Annotated[ResearchService, Depends(get_research_service)]


def get_generation_service() -> ResearchGenerationService:
    return ResearchGenerationService()


GenerationServiceDependency = Annotated[ResearchGenerationService, Depends(get_generation_service)]


@router.get("/reports", response_model=ResearchReportListResponse, summary="查询已有 AI 研究报告")
def list_reports(service: ResearchServiceDependency) -> ResearchReportListResponse:
    return service.list_reports()


@router.get("/reports/{symbol}", response_model=ResearchReportDetail, summary="读取单只股票研究报告")
def get_report(
    service: ResearchServiceDependency,
    symbol: str = Path(pattern=r"^\d{6}$"),
) -> ResearchReportDetail:
    return service.get_report(symbol)


@router.post("/reports/{symbol}/generate", response_model=GenerationTaskResponse, summary="创建 AI 研究报告生成任务")
def generate_report(background_tasks: BackgroundTasks, service: GenerationServiceDependency, symbol: str = Path(pattern=r"^\d{6}$")) -> GenerationTaskResponse:
    return service.create_task(symbol, background_tasks)


@router.get("/tasks/{task_id}", response_model=GenerationTaskResponse, summary="查询研究报告生成任务")
def get_generation_task(task_id: str, service: GenerationServiceDependency) -> GenerationTaskResponse:
    return service.get_task(task_id)


@router.get("/tasks/{task_id}/result", response_model=GenerationResultResponse, summary="读取生成任务结果")
def get_generation_result(task_id: str, service: GenerationServiceDependency) -> GenerationResultResponse:
    return service.get_result(task_id)
