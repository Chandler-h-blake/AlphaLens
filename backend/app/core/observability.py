import time
from collections import defaultdict, deque
from threading import Lock
from uuid import uuid4

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Attach a safe correlation id and server timing to every API response."""

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID", "")
        if not request_id or len(request_id) > 64 or not request_id.replace("-", "").replace("_", "").isalnum():
            request_id = str(uuid4())
        started_at = time.perf_counter()
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time-Ms"] = f"{(time.perf_counter() - started_at) * 1000:.1f}"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; connect-src 'self'; img-src 'self' data:; "
            "style-src 'self' 'unsafe-inline'; font-src 'self' data:; "
            "frame-ancestors 'none'; base-uri 'self'"
        )
        return response


class PublicWriteRateLimitMiddleware(BaseHTTPMiddleware):
    """Keep public refresh and LLM endpoints usable without exposing unlimited spend."""

    def __init__(
        self,
        app,
        *,
        enabled: bool,
        market_refresh_limit_per_minute: int,
        report_generation_limit_per_hour: int,
    ) -> None:
        super().__init__(app)
        self.enabled = enabled
        self.rules = {
            "market_refresh": (market_refresh_limit_per_minute, 60),
            "report_generation": (report_generation_limit_per_hour, 3600),
        }
        self.requests: dict[tuple[str, str], deque[float]] = defaultdict(deque)
        self.lock = Lock()

    async def dispatch(self, request: Request, call_next) -> Response:
        rule_name = self._rule_name(request)
        if not self.enabled or rule_name is None:
            return await call_next(request)

        limit, window_seconds = self.rules[rule_name]
        client_id = self._client_id(request)
        now = time.monotonic()
        key = (rule_name, client_id)
        with self.lock:
            timestamps = self.requests[key]
            while timestamps and now - timestamps[0] >= window_seconds:
                timestamps.popleft()
            if len(timestamps) >= limit:
                retry_after = max(1, int(window_seconds - (now - timestamps[0])))
                return JSONResponse(
                    status_code=429,
                    content={"detail": {"code": "RATE_LIMITED", "message": "请求过于频繁，请稍后再试。"}},
                    headers={"Retry-After": str(retry_after)},
                )
            timestamps.append(now)
        return await call_next(request)

    @staticmethod
    def _rule_name(request: Request) -> str | None:
        if request.method != "POST":
            return None
        path = request.url.path
        if path in {"/api/market/dashboard", "/api/market/funds", "/api/industry/rotation/refresh"}:
            return "market_refresh"
        if path == "/api/reviews/generate":
            return "report_generation"
        if path.startswith("/api/market/stocks/") and path.endswith("/refresh"):
            return "market_refresh"
        if path.startswith("/api/research/reports/") and path.endswith("/generate"):
            return "report_generation"
        return None

    @staticmethod
    def _client_id(request: Request) -> str:
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Reverse proxies append the direct client address. Selecting the last
            # value avoids trusting an arbitrary first value supplied by a client.
            return forwarded_for.rsplit(",", maxsplit=1)[-1].strip()
        return request.client.host if request.client else "unknown"
