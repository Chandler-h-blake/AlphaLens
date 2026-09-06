from tests.api_client import ApiClient


client = ApiClient()


def test_top_pool_returns_ranked_factor_data() -> None:
    response = client.get("/api/factors/top30")

    assert response.status_code == 200
    payload = response.json()
    assert payload["source"] == "AlphaLens 因子评分快照"
    assert payload["total"] >= 1
    assert payload["items"][0]["rank"] == 1
    assert payload["items"][0]["symbol"] == "002558"
    assert payload["items"][0]["industry"] == "传媒"
    assert "momentum_20d" in payload["items"][0]["factor_values"]


def test_top_pool_filters_by_stock_code() -> None:
    response = client.get("/api/factors/top30", params={"keyword": "300308"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["symbol"] == "300308"


def test_top_pool_rejects_invalid_limit() -> None:
    response = client.get("/api/factors/top30", params={"limit": 0})

    assert response.status_code == 422


def test_factor_overview_returns_validated_metrics() -> None:
    response = client.get("/api/factors/overview")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] >= 1
    assert payload["items"][0]["factor"] == "revenue_growth_yoy"
    assert payload["items"][0]["weight"] == 0.22
