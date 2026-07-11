from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import Depends, FastAPI, Response, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from db import engine, get_session
from logger import logger
from models import Message


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Probe the database once at boot so a bad DATABASE_URL shows up in the logs
    # immediately rather than on the first user request. We log and continue
    # rather than raise: crashing here would put the pod in CrashLoopBackOff
    # whenever Postgres is merely slow to start. The readiness probe below is
    # what keeps traffic away until the database is actually reachable.
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


class EchoRequest(BaseModel):
    message: str


class MessageCreate(BaseModel):
    body: str = Field(min_length=1, max_length=500)


class MessageOut(BaseModel):
    # from_attributes lets FastAPI serialise the SQLAlchemy object directly.
    model_config = ConfigDict(from_attributes=True)

    id: int
    body: str
    created_at: datetime


@app.get("/")
def read_root():
    logger.info("Root endpoint called")
    return {"message": "Hello from FastAPI on the way to EKS"}


@app.get("/health")
def health_check():
    """Liveness: is the process alive? Deliberately does NOT touch the database.

    If liveness checked Postgres, a database blip would make Kubernetes kill and
    restart every pod — which cannot fix a database problem and only makes it worse.
    """
    logger.debug("Liveness probe called")
    return {"status": "ok"}


@app.get("/health/ready")
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


@app.post("/echo")
def echo(payload: EchoRequest):
    logger.info(f"Echo endpoint called with message= {payload.message}")
    return {"you_sent": payload.message}


@app.post("/messages", response_model=MessageOut, status_code=status.HTTP_201_CREATED)
async def create_message(
    payload: MessageCreate, session: AsyncSession = Depends(get_session)
):
    message = Message(body=payload.body)
    session.add(message)
    await session.commit()
    # Fetch the columns Postgres filled in for us (id, created_at).
    await session.refresh(message)
    logger.info(f"Stored message id={message.id}")
    return message


@app.get("/messages", response_model=list[MessageOut])
async def list_messages(
    limit: int = 20, session: AsyncSession = Depends(get_session)
):
    result = await session.execute(
        select(Message).order_by(Message.created_at.desc()).limit(limit)
    )
    messages = result.scalars().all()
    logger.info(f"Returned {len(messages)} messages")
    return messages


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)