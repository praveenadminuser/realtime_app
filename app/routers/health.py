"""Root and health probes. Kept in their own router so infrastructure endpoints don't
mingle with business ones."""
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_session
from logger import logger

router = APIRouter(tags=["health"])


@router.get("/")
def read_root():
    logger.info("Root endpoint called")
    return {"message": "Hello from FastAPI on the way to EKS"}


@router.get("/health")
def health_check():
    """Liveness: is the process alive? Deliberately does NOT touch the database.

    If liveness checked Postgres, a database blip would make Kubernetes kill and
    restart every pod — which cannot fix a database problem and only makes it worse.
    """
    logger.debug("Liveness probe called")
    return {"status": "ok"}


@router.get("/health/ready")
async def readiness_check(
    response: Response, session: AsyncSession = Depends(get_session)
):
    """Readiness: can this pod actually serve traffic? This one does hit the database.

    Returning 503 pulls the pod out of the Service's endpoints without killing it,
    so it rejoins automatically once the database comes back.
    """
    try:
        await session.execute(text("SELECT 1"))
        return {"status": "ready", "database": "ok"}
    except Exception as exc:
        logger.error(f"Readiness check failed: {exc}")
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "not ready", "database": "unreachable"}