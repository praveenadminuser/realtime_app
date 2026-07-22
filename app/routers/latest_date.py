"""Endpoint exposing the cached latest-date file.

Deliberately a sync `def`, not `async def`: the handler does blocking file I/O, and FastAPI
runs sync path operations in a threadpool, so the event loop is never blocked. Writing it
`async def` would run the blocking read ON the event loop and stall every other request.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status

from schemas.latest_date import LatestDataResponse, LatestDateResponse
from services import latest_date_service

router = APIRouter(tags=["latest-date"])


@router.get("/latest-date", response_model=LatestDateResponse)
def read_latest_date() -> LatestDateResponse:
    try:
        data = latest_date_service.get_latest_date()
    except latest_date_service.LatestDateError as exc:
        # The file being missing/corrupt is an operational problem, not a client error —
        # 503 says "the server can't serve this right now", not "you did something wrong".
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        )

    return LatestDateResponse(
        latest_date=data["latest_date"],
        source=data["source"],
        loaded_at=data["loaded_at"],
        file_modified_at=datetime.fromtimestamp(data["mtime"], tz=timezone.utc),
    )


@router.get("/latest-date/data", response_model=LatestDataResponse)
def read_latest_data() -> LatestDataResponse:
    """Return the CONTENT for the current latest date. Chains two caches: the TTL-cached
    pointer (which date?) and the LRU-cached per-date file (that date's immutable data)."""
    try:
        result = latest_date_service.get_latest_data()
    except latest_date_service.LatestDateError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        )
    return LatestDataResponse(**result)