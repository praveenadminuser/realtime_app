"""Phase B: the retrieval + generation chain.

Wires retriever → grounding prompt → LLM using LangChain's standard building blocks. The
result carries both the generated `answer` and the `context` (the chunks used), so the
service can return citations.
"""
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

from config import settings
from rag.llm import get_llm
from rag.vectorstore import get_vectorstore

# THE grounding prompt — the hallucination guard. It forbids answering from the model's own
# training data: only the retrieved {context} is allowed, and "I don't know" is required
# when the answer isn't there. Without this instruction, RAG's whole point evaporates.
_SYSTEM_PROMPT = (
    "You are a helpful assistant answering questions about the user's documents. "
    "Use ONLY the context below to answer. If the answer is not contained in the "
    "context, say you don't know — do not use outside knowledge and do not make "
    "anything up.\n\n"
    "Context:\n{context}"
)


def build_rag_chain(top_k: int | None = None):
    """Assemble the chain. Cheap to build per request; memoize later if it matters."""
    llm = get_llm()
    retriever = get_vectorstore().as_retriever(
        search_kwargs={"k": top_k or settings.rag_top_k}
    )
    prompt = ChatPromptTemplate.from_messages(
        [("system", _SYSTEM_PROMPT), ("human", "{input}")]
    )
    # "stuff" = concatenate the retrieved chunks into the prompt's {context}. Simple and
    # right for top-k small; other strategies (map-reduce, refine) exist for many/large docs.
    combine_docs = create_stuff_documents_chain(llm, prompt)
    # create_retrieval_chain runs the retriever, feeds the chunks to combine_docs, and
    # returns {"input", "context": [chunks], "answer": str}.
    return create_retrieval_chain(retriever, combine_docs)