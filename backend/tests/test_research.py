from tests.api_client import ApiClient


client = ApiClient()


def test_reports_list_persisted_markdown_reports() -> None:
    response = client.get("/api/research/reports")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] >= 5
    assert any(item["symbol"] == "002558" for item in payload["items"])


def test_report_detail_returns_sources_and_markdown() -> None:
    response = client.get("/api/research/reports/002558")

    assert response.status_code == 200
    payload = response.json()
    assert payload["name"] == "巨人网络"
    assert payload["content_markdown"].startswith("#")
    assert payload["sources"]
    assert "不构成投资建议" in payload["disclaimer"]


def test_report_detail_returns_404_when_report_is_absent() -> None:
    response = client.get("/api/research/reports/000001")

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "RESOURCE_NOT_FOUND"
