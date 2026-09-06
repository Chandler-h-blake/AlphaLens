from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends

from app.schemas.dashboard import ReviewResultResponse, ReviewTaskResponse, SnapshotResponse, SystemStatusResponse
from app.services.dashboard_service import DashboardService
from app.services.review_service import ReviewService

router = APIRouter()
review_router = APIRouter()


def get_dashboard_service() -> DashboardService:
    return DashboardService()


DashboardDependency = Annotated[DashboardService, Depends(get_dashboard_service)]


@router.get("/dashboard", response_model=SnapshotResponse)
def get_dashboard(service: DashboardDependency) -> SnapshotResponse:
    return service.get("dashboard")


@router.post("/dashboard", response_model=SnapshotResponse)
def refresh_dashboard(service: DashboardDependency) -> SnapshotResponse:
    return service.refresh("dashboard")


@router.get("/funds", response_model=SnapshotResponse)
def get_funds(service: DashboardDependency) -> SnapshotResponse:
    return service.get("funds")


@router.post("/funds", response_model=SnapshotResponse)
def refresh_funds(service: DashboardDependency) -> SnapshotResponse:
    return service.refresh("funds")


@review_router.post("/generate", response_model=ReviewTaskResponse)
def generate_review(background_tasks: BackgroundTasks) -> ReviewTaskResponse:
    return ReviewService().create(background_tasks)


@review_router.get("/tasks/{task_id}", response_model=ReviewTaskResponse)
def get_review_task(task_id: str) -> ReviewTaskResponse:
    return ReviewService().get(task_id)


@review_router.get("/tasks/{task_id}/result", response_model=ReviewResultResponse)
def get_review_result(task_id: str) -> ReviewResultResponse:
    return ReviewService().result(task_id)
