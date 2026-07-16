"""Application entrypoint. Wires the app together; contains no endpoint logic itself.

Each resource lives in its own router under routers/. Adding a feature means adding a
router (and, if it has real logic, a service + schema) and one include_router line here —
nothing in this file grows per-endpoint.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from config import settings
from db import engine
from logger import logger
from routers import health, messages, users


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Probe the database once at boot so a bad config shows up in the logs immediately
    # rather than on the first user request. We log and continue rather than raise:
    # crashing here would put the pod in CrashLoopBackOff whenever Postgres is merely
    # slow to start. The readiness probe is what keeps traffic away until the database
    # is actually reachable.
    #
    # safe_url, not the real one: the password is masked so it never reaches a log
    # aggregator. Logging the target answers "which database am I pointed at?" — the
    # first question in every connection bug.
    logger.info(f"Connecting to {settings.safe_url}")
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Database reachable at startup")
    except Exception as exc:
        logger.error(f"Database unreachable at startup: {exc}")

    yield

    await engine.dispose()
    logger.info("Database connection pool closed")


app = FastAPI(
    title="Realtime Application",
    description="A simple FastAPI app — starting point for AWS EKS deployment.",
    version="0.2.0",
    lifespan=lifespan,
)

# Register routers. New resources get one line each.
app.include_router(health.router)
app.include_router(users.router)
app.include_router(messages.router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)