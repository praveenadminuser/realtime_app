from fastapi import FastAPI
from pydantic import BaseModel
from logger import logger

app = FastAPI(
    title="Realtime Application",
    description="A simple FastAPI app — starting point for AWS EKS deployment.",
    version="0.1.0",
)


class EchoRequest(BaseModel):
    message: str


@app.get("/")
def read_root():
    logger.info("Root endpoint called")
    return {"message": "Hello from FastAPI on the way to EKS"}


@app.get("/health")
def health_check():
    """Liveness/readiness probe endpoint (used later by Kubernetes)."""
    logger.debug('This is debug message.')
    return {"status": "ok"}


@app.post("/echo")
def echo(payload: EchoRequest):
    logger.info(f"Echo endpoint called with message= {payload.message}")
    return {"you_sent": payload.message}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
