"""The /metrics endpoint Prometheus scrapes.

Public (no auth) — a Prometheus scraper carries no bearer token. Returns the current values
of every metric recorded by MetricsMiddleware, in Prometheus's text exposition format.
"""
from fastapi import APIRouter
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from starlette.responses import Response

router = APIRouter(tags=["metrics"])


@router.get("/metrics")
def metrics() -> Response:
    # generate_latest() serialises the default registry; CONTENT_TYPE_LATEST is the exact
    # media type Prometheus expects (text/plain; version=0.0.4).
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)