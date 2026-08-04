"""Chat LLM factory. Swapping Ollama for Bedrock/OpenAI later is a change HERE only —
the chain and service don't know which model they're talking to. That's LangChain's point.
"""
from langchain_ollama import ChatOllama

from config import settings


def get_llm() -> ChatOllama:
    return ChatOllama(
        model=settings.ollama_llm_model,
        base_url=settings.ollama_base_url,
        # temperature=0: we want faithful, deterministic answers grounded in the retrieved
        # context — not creative writing. Higher temperature invites hallucination.
        temperature=0,
    )