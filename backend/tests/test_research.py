from tests.api_client import ApiClient


client = ApiClient()


def test_reports_list_seed_markdown_reports() -> None:
    response = client.get("/api/research/reports")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 5
    assert payload["items"][0]["symbol"] in {"002466", "002558", "002709", "300308", "603986"}


def test_report_detail_returns_sources_and_markdown() -> None:
    response = client.get("/api/research/reports/002558")

    assert response.status_code == 200
    payload = response.json()
    assert payload["name"] == "巨人网络"
    assert "多 Agent 深度投研报告" in payload["content_markdown"]
    assert len(payload["sources"]) == 2
    assert "不构成投资建议" in payload["disclaimer"]


def test_report_detail_returns_404_when_report_is_absent() -> None:
    response = client.get("/api/research/reports/000001")

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "RESOURCE_NOT_FOUND"
