"""Prometheus metrics middleware.

Records two standard HTTP metrics for every request, which the /metrics endpoint
(routers/metrics.py) then exposes for Prometheus to scrape:

  http_requests_total          Counter   — how many requests, by method/endpoint/status
  http_request_duration_seconds Histogram — latency distribution, by method/endpoint

Together these give you the "RED" signals (Rate, Errors, Duration) for every endpoint.
"""
import time

from prometheus_client import Counter, Histogram
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

# Metric objects are module-level singletons (Prometheus registers them once at import).
# Label sets are kept LOW-cardinality on purpose — see the endpoint note in dispatch().
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests.",
    ["method", "endpoint", "status"],
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds.",
    ["method", "endpoint"],
    # Buckets tuned for a web API (seconds). Prometheus computes percentiles (p50/p95/p99)
    # from these, so they should straddle your expected latencies. Default buckets top out
    # at 10s which is fine here.
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

METRICS_PATH = "/metrics"


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Don't measure the scrape endpoint itself — it would inflate its own metrics every
        # time Prometheus polls (every ~15s).
        if request.url.path == METRICS_PATH:
            return await call_next(request)

        start = time.perf_counter()
        status = 500  # assume failure; overwritten on success. So an exception still counts.
        try:
            response = await call_next(request)
            status = response.status_code
            return response
        finally:
            elapsed = time.perf_counter() - start
            # ROUTE TEMPLATE, never the raw path. "/users/{user_id}" is one label value;
            # "/users/123", "/users/124", … would be MILLIONS — a cardinality explosion that
            # can OOM Prometheus. Unmatched paths (404s, scanners hitting random URLs) all
            # collapse to the constant "unmatched" for the same reason.
            route = request.scope.get("route")
            endpoint = getattr(route, "path", None) or "unmatched"
            REQUEST_LATENCY.labels(request.method, endpoint).observe(elapsed)
            REQUEST_COUNT.labels(request.method, endpoint, status).inc()
