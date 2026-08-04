"""RAG request/response contracts."""
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(min_length=1)
    # Optional per-request override of how many chunks to retrieve.
    top_k: int | None = Field(default=None, ge=1, le=20)


class Source(BaseModel):
    """A citation: which document + page a retrieved chunk came from."""

    source: str | None = None
    page: int | None = None


class QueryResponse(BaseModel):
    answer: str
    # The chunks the answer was grounded in — makes the response traceable, not a black box.
    sources: list[Source]


class IngestResponse(BaseModel):
    filename: str
    chunks_indexed: int


class StatusResponse(BaseModel):
    ollama: bool
    ollama_models: list[str]
    chroma: bool
    indexed_chunks: int | None = None