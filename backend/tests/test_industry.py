from tests.api_client import ApiClient


client = ApiClient()


def test_industry_rotation_returns_ranked_data() -> None:
    response = client.get("/api/industry/rotation")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] >= 1
    assert payload["items"][0]["rank_1m"] == 1
    assert payload["items"][0]["industry_name"] == "电子"


def test_industry_dates_returns_available_date() -> None:
    response = client.get("/api/industry/rotation/dates")

    assert response.status_code == 200
    assert response.json()["items"] == ["2026-07-06"]
