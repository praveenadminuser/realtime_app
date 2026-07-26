"""Request timing + access logging middleware.

For every request it records the method, the endpoint, the status, and how long it took in
milliseconds — logged, and echoed back in response headers. This is the one place that sees
*every* request, which is exactly why timing belongs here rather than in each endpoint.
"""
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from logger import logger


class TimingMiddleware(BaseHTTPMiddleware):
    """Times each request and logs `METHOD endpoint -> status in N ms`.

    Uses Starlette's BaseHTTPMiddleware — simple and fine for this. (The lower-level
    "pure ASGI middleware" is more efficient and plays better with streaming responses and
    background tasks; worth switching to if this ever becomes a hot path. Noted, not needed
    yet.)
    """

    def __init__(self, app, header_name: str = "X-Process-Time-Ms", slow_ms: float = 1000.0):
        super().__init__(app)
        self.header_name = header_name
        self.slow_ms = slow_ms  # requests slower than this are logged at WARNING

    async def dispatch(self, request: Request, call_next):
        # A correlation id: reuse an inbound one (set by a gateway/nginx) or mint one. Every
        # log line for this request carries it, so you can grep one request's whole path —
        # essential once traffic is spread across multiple pods.
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:12]

        # perf_counter: monotonic, high-resolution — the correct clock for durations (never
        # time.time(), which can jump when the wall clock is adjusted).
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            # Log timing even when the endpoint raises, then re-raise so error handling is
            # unchanged. Without this, failed requests would have no timing record.
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            logger.exception(
                f"[{request_id}] {request.method} {request.url.path} "
                f"FAILED after {elapsed_ms:.1f} ms"
            )
            raise

        elapsed_ms = (time.perf_counter() - start) * 1000.0

        # Prefer the ROUTE TEMPLATE (/users/{user_id}) over the raw path (/users/123). Raw
        # paths would explode cardinality in logs/metrics — every id a distinct "endpoint".
        # The route is set on the scope during routing (inside call_next); absent for a 404.
        route = request.scope.get("route")
        endpoint = getattr(route, "path", None) or request.url.path

        # Surface the timing to the caller too — visible in curl -i / the browser Network tab.
        response.headers[self.header_name] = f"{elapsed_ms:.1f}"
        response.headers["X-Request-ID"] = request_id

        line = (
            f"[{request_id}] {request.method} {endpoint} "
            f"-> {response.status_code} in {elapsed_ms:.1f} ms"
        )
        # A slow request is worth flagging louder than the routine access log.
        if elapsed_ms >= self.slow_ms:
            logger.warning(f"SLOW {line}")
        else:
            logger.info(line)

        return response