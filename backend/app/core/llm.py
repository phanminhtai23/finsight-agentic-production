"""Google Gemini provider — chat model, embeddings, and RAG-port adapters.

Free tier via Google AI Studio (set ``GOOGLE_API_KEY``). The adapters expose the LangChain
objects through the narrow ``Embedder`` / ``TextGenerator`` ports the RAG layer depends on.
"""

import asyncio
from collections.abc import AsyncIterator
from functools import lru_cache

from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.core.resilience import call_with_retry, is_transient_error

log = get_logger(__name__)


def build_chat_model(
    settings: Settings | None = None, *, temperature: float = 0.2
) -> BaseChatModel:
    settings = settings or get_settings()
    return ChatGoogleGenerativeAI(
        model=settings.llm_model,
        google_api_key=settings.google_api_key,
        temperature=temperature,
    )


def build_embeddings(settings: Settings | None = None) -> Embeddings:
    settings = settings or get_settings()
    return GoogleGenerativeAIEmbeddings(
        model=settings.embedding_model,
        google_api_key=settings.google_api_key,
    )


class GeminiEmbedder:
    """Adapts LangChain embeddings to the ``Embedder`` port."""

    def __init__(self, embeddings: Embeddings, dim: int) -> None:
        self._embeddings = embeddings
        self.dim = dim

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return await call_with_retry(
            self._embeddings.aembed_documents, texts, label="embed_documents"
        )

    async def embed_query(self, text: str) -> list[float]:
        return await call_with_retry(self._embeddings.aembed_query, text, label="embed_query")


class GeminiTextGenerator:
    """Adapts a LangChain chat model to the ``TextGenerator`` port."""

    def __init__(self, model: BaseChatModel) -> None:
        self._model = model

    async def generate(self, prompt: str) -> str:
        resp = await call_with_retry(
            self._model.ainvoke, [HumanMessage(content=prompt)], label="llm_generate"
        )
        return self._to_text(resp.content)

    @staticmethod
    def _to_text(content: object) -> str:
        """Flatten LangChain message content (str or list of content blocks) to plain text."""
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts: list[str] = []
            for block in content:
                if isinstance(block, str):
                    parts.append(block)
                elif isinstance(block, dict) and block.get("type") == "text":
                    parts.append(block.get("text", ""))
            return "".join(parts)
        return str(content)


@lru_cache
def get_embedder() -> GeminiEmbedder:
    settings = get_settings()
    return GeminiEmbedder(build_embeddings(settings), dim=settings.embedding_dim)


@lru_cache
def get_chat_model() -> BaseChatModel:
    return build_chat_model()


@lru_cache
def get_text_generator() -> GeminiTextGenerator:
    return GeminiTextGenerator(get_chat_model())


async def stream_chat(model: BaseChatModel, prompt: str) -> AsyncIterator[str]:
    """Yield answer text chunks as the model generates them (token streaming).

    Retries only while *no* token has been emitted yet (e.g. a 429 when opening the stream),
    so a transient blip at connect time recovers without ever duplicating mid-stream tokens.
    """
    settings = get_settings()
    attempt = 0
    while True:
        attempt += 1
        emitted = 0
        try:
            async for chunk in model.astream([HumanMessage(content=prompt)]):
                text = GeminiTextGenerator._to_text(chunk.content)
                if text:
                    emitted += 1
                    yield text
            return
        except Exception as exc:  # noqa: BLE001
            # Once tokens are flowing, or retries/transience are exhausted, propagate.
            if emitted or attempt >= settings.llm_max_attempts or not is_transient_error(exc):
                raise
            delay = min(
                settings.llm_retry_initial_seconds * (2 ** (attempt - 1)),
                settings.llm_retry_max_seconds,
            )
            log.warning("retrying_stream_open", attempt=attempt, sleep=delay, error=str(exc))
            await asyncio.sleep(delay)
