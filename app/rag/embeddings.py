"""Embedding model factory — the one place the embedding model is chosen.

Used by BOTH phases (ingest and query), which is exactly why it lives in one function: the
same model MUST embed documents and questions, or similarity search compares incomparable
vectors. Change the model here and you must re-index everything. See RAG.md.
"""
from langchain_ollama import OllamaEmbeddings

from config import settings


def get_embeddings() -> OllamaEmbeddings:
    return OllamaEmbeddings(
        model=settings.ollama_embed_model,
        base_url=settings.ollama_base_url,
    )