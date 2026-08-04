"""RAG endpoints: ingest a PDF, ask a question, check status.

HTTP-only — parsing, chunking, retrieval and generation all live in rag/service.py. External
deps (Ollama, Chroma) being down surfaces as 503, not a 500 stack trace.

NOTE: left unauthenticated for now so it's easy to try. In production, protect /ingest at
minimum (who can add documents) — add `dependencies=[Depends(get_current_active_user)]` to
the router, exactly like the messages router.
"""
from fastapi import APIRouter, File, HTTPException, UploadFile, status

from logger import logger
from rag import service
from schemas.rag import IngestResponse, QueryRequest, QueryResponse, StatusResponse

router = APIRouter(prefix="/rag", tags=["rag"])


@router.post("/ingest", response_model=IngestResponse)
async def ingest(file: UploadFile = File(...)) -> IngestResponse:
    """Phase A: load → chunk → embed → store the uploaded PDF."""
    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="only PDF files are supported",
        )
    data = await file.read()
    try:
        chunks = await service.ingest_pdf(file.filename, data)
    except Exception as exc:
        # A bad PDF is the client's fault (422); a dep being down is ours (503). We can't
        # always tell them apart cheaply, so 503 with the message is the pragmatic choice.
        logger.error(f"[rag] ingest failed for {file.filename}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"ingestion failed: {exc}",
        )
    return IngestResponse(filename=file.filename, chunks_indexed=chunks)


@router.post("/query", response_model=QueryResponse)
async def query(payload: QueryRequest) -> QueryResponse:
    """Phase B: retrieve → augment → generate. Returns the answer and its source chunks."""
    try:
        result = await service.answer_question(payload.question, payload.top_k)
    except Exception as exc:
        logger.error(f"[rag] query failed: {exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"query failed: {exc}",
        )
    return QueryResponse(**result)


@router.get("/status", response_model=StatusResponse)
async def rag_status() -> StatusResponse:
    """Are Ollama and Chroma reachable, and how many chunks are indexed?"""
    return StatusResponse(**await service.status())