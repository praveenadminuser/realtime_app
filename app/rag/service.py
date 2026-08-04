"""The two public RAG operations: ingest a PDF, and answer a question.

The router calls only these. Blocking work (PDF parse + synchronous embedding calls) is
pushed off the event loop with asyncio.to_thread; the query path uses LangChain's native
async (ainvoke).
"""
import asyncio
import os
import tempfile

import httpx

from config import settings
from logger import logger
from rag.chain import build_rag_chain
from rag.loaders import load_and_split
from rag.vectorstore import get_vectorstore


def _ingest_pdf_sync(filename: str, data: bytes) -> int:
    """Blocking: PyPDFLoader needs a real file path, and add_documents embeds each chunk
    via synchronous Ollama calls. Run via asyncio.to_thread so the event loop isn't blocked.
    """
    # NamedTemporaryFile(delete=False) so PyPDFLoader can reopen it by path; we unlink after.
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(data)
        tmp_path = tmp.name
    try:
        chunks = load_and_split(tmp_path, source_name=filename)
        # Deterministic ids (filename:index) so re-ingesting the same PDF UPSERTS rather than
        # duplicating — the idempotency principle again. (Exact upsert semantics depend on
        # the langchain-chroma version; verify on first real run.)
        ids = [f"{filename}:{c.metadata['chunk']}" for c in chunks]
        get_vectorstore().add_documents(chunks, ids=ids)
        logger.info(f"[rag] ingested {len(chunks)} chunks from {filename}")
        return len(chunks)
    finally:
        os.unlink(tmp_path)


async def ingest_pdf(filename: str, data: bytes) -> int:
    return await asyncio.to_thread(_ingest_pdf_sync, filename, data)


async def answer_question(question: str, top_k: int | None = None) -> dict:
    chain = build_rag_chain(top_k)
    result = await chain.ainvoke({"input": question})
    # Turn the retrieved chunks into lightweight citations for the response.
    sources = [
        {"source": doc.metadata.get("source"), "page": doc.metadata.get("page"), 
         'page_content': doc.page_content }
        for doc in result.get("context", [])
    ]

    logger.info('The retrieved context info from vector store is below')
    for src in sources:
        logger.info(f"page number: {src['page']} and page_content {src['page_content']}")

    logger.info(f"[rag] answered question using {len(sources)} chunks")
    return {"answer": result["answer"], "sources": sources}


async def status() -> dict:
    """Readiness of the two external deps + how many chunks are indexed. Never raises —
    reports what's up so the endpoint can show a partial picture (graceful degradation)."""
    ollama_ok, models = False, []
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{settings.ollama_base_url}/api/tags")
            resp.raise_for_status()
            models = [m.get("name") for m in resp.json().get("models", [])]
            ollama_ok = True
    except Exception as exc:
        logger.warning(f"[rag] ollama status check failed: {exc}")

    chroma_ok, indexed = False, None
    try:
        # _collection is the underlying chromadb collection; count() is a cheap size check.
        indexed = get_vectorstore()._collection.count()
        chroma_ok = True
    except Exception as exc:
        logger.warning(f"[rag] chroma status check failed: {exc}")

    return {
        "ollama": ollama_ok,
        "ollama_models": models,
        "chroma": chroma_ok,
        "indexed_chunks": indexed,
    }