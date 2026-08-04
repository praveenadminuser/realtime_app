"""Phase A steps 1–2: load a PDF into text and split it into chunks.

Kept separate from storage so the "how we cut documents" logic is swappable without
touching the vector store.
"""
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import settings


def load_and_split(pdf_path: str, source_name: str) -> list[Document]:
    """PDF file path -> list of chunk Documents, each carrying source + page metadata.

    PyPDFLoader yields one Document PER PAGE (so page numbers survive → citations).
    RecursiveCharacterTextSplitter then splits on natural boundaries (paragraph, then
    sentence, then word) rather than mid-word — that's the "recursive" part.
    """
    pages = PyPDFLoader(pdf_path).load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.rag_chunk_size,
        chunk_overlap=settings.rag_chunk_overlap,
    )
    chunks = splitter.split_documents(pages)

    # PyPDFLoader stamps `source` with the (temp) file path; overwrite it with the real
    # upload name so citations show "report.pdf", not "/tmp/xyz.pdf". Add a chunk index too.
    for i, chunk in enumerate(chunks):
        chunk.metadata["source"] = source_name
        chunk.metadata["chunk"] = i
    return chunks