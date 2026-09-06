import asyncio
from collections import deque

import httpx
from fastapi import FastAPI

from app.core.observability import PublicWriteRateLimitMiddleware, RequestContextMiddleware


def test_rate_limit_rules_only_match_expensive_write_endpoints() -> None:
    class Request:
        method = "POST"

        class Url:
            path = "/api/research/reports/002558/generate"

        url = Url()

    assert PublicWriteRateLimitMiddleware._rule_name(Request()) == "report_generation"

    Request.url.path = "/api/market/stocks/002558/refresh"
    assert PublicWriteRateLimitMiddleware._rule_name(Request()) == "market_refresh"

    Request.method = "GET"
    assert PublicWriteRateLimitMiddleware._rule_name(Request()) is None


def test_rate_limit_state_can_discard_expired_requests() -> None:
    timestamps = deque([1.0, 2.0, 70.0])
    now = 80.0
    while timestamps and now - timestamps[0] >= 60:
        timestamps.popleft()
    assert list(timestamps) == [70.0]


def test_rate_limited_response_keeps_request_and_security_headers() -> None:
    app = FastAPI()
    app.add_middleware(PublicWriteRateLimitMiddleware, enabled=True, market_refresh_limit_per_minute=1, report_generation_limit_per_hour=1)
    app.add_middleware(RequestContextMiddleware)

    @app.post("/api/research/reports/002558/generate")
    def generate() -> dict[str, bool]:
        return {"ok": True}

    async def request_twice() -> tuple[httpx.Response, httpx.Response]:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            return await client.post("/api/research/reports/002558/generate"), await client.post("/api/research/reports/002558/generate")

    allowed, limited = asyncio.run(request_twice())

    assert allowed.status_code == 200
    assert limited.status_code == 429
    assert limited.headers["x-request-id"]
    assert limited.headers["x-content-type-options"] == "nosniff"
    assert "frame-ancestors 'none'" in limited.headers["content-security-policy"]
