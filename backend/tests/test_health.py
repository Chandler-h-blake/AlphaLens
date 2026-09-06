from app.core.config import get_settings
from tests.api_client import ApiClient


client = ApiClient()


def test_health_returns_service_status() -> None:
    response = client.get("/api/health")
    settings = get_settings()

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "environment": settings.app_env}
    assert response.headers["x-request-id"]
    assert float(response.headers["x-response-time-ms"]) >= 0
    assert response.headers["x-content-type-options"] == "nosniff"


def test_liveness_and_csv_readiness_are_available() -> None:
    liveness = client.get("/api/health/live")
    readiness = client.get("/api/health/ready")
    settings = get_settings()

    assert liveness.status_code == 200
    assert readiness.status_code == 200
    assert readiness.json() == {
        "status": "ok",
        "environment": settings.app_env,
        "database": "ok" if settings.data_backend == "database" else "not_required",
    }


def test_health_endpoints_support_head_requests() -> None:
    response = client.request("HEAD", "/api/health")

    assert response.status_code == 200
    assert response.content == b""
