"""Chroma vector store connection.

Connects to Chroma in SERVER mode (an HttpClient), not embedded. Embedded Chroma writes to
a local dir inside one process — with multiple pods each would hold its OWN index, so an
ingest on pod A would be invisible to a query on pod B. Server mode = one shared index for
all pods, the same multi-pod reasoning that made us pick Redis over lru_cache. See RAG.md.
"""
import chromadb
from langchain_chroma import Chroma

from config import settings
from rag.embeddings import get_embeddings


def get_vectorstore() -> Chroma:
    # HttpClient talks to a running Chroma server (locally installed, or a container).
    client = chromadb.HttpClient(host=settings.chroma_host, port=settings.chroma_port)
    return Chroma(
        client=client,
        collection_name=settings.rag_collection,
        # The embedding_function is what Chroma calls to vectorise a query at search time.
        # It MUST be the same model used at ingest — that's why both go through get_embeddings.
        embedding_function=get_embeddings(),
    )