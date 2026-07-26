"""Cross-cutting HTTP middleware, wired in one place.

main.py calls register_middlewares(app) and nothing else — every middleware is registered
here, so adding one (CORS, gzip, auth-context, Prometheus metrics) is a one-line change that
doesn't touch main.py or any endpoint.
"""
from fastapi import FastAPI

from middleware.metrics import MetricsMiddleware
from middleware.timing import TimingMiddleware


def register_middlewares(app: FastAPI) -> None:
    # NOTE on order: middleware added LAST runs FIRST on the way in (it's a stack). With
    # these two it doesn't matter — both just observe. When you add an outermost concern
    # (e.g. a request-id you want on every log line), add it last so it wraps the rest.
    app.add_middleware(TimingMiddleware)  # human-readable access log per request
    app.add_middleware(MetricsMiddleware)  # Prometheus counters/histograms for /metrics