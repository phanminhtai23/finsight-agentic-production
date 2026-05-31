"""Streaming chat — token-by-token answers with optional 'thinking' steps.

A focused linear pipeline (retrieve → optional web → optional thinking → answer) optimised
for streaming UX. The full critic-loop multi-agent graph remains the non-streaming path.
"""

import uuid
from collections.abc import AsyncIterator

from langchain_core.language_models import BaseChatModel
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.agents import prompts
from app.agents.nodes import RetrieverFactory, build_citations, format_evidence
from app.agents.state import EvidenceItem
from app.agents.web import WebSearch
from app.core.config import get_settings
from app.core.guardrails import apply_output_disclaimer, check_input, refusal_message
from app.core.llm import stream_chat
from app.core.logging import get_logger
from app.core.metrics import guardrail_blocks_total
from app.rag.ports import TextGenerator
from app.repositories.conversation_repository import ConversationRepository
from app.services.visualization_service import VisualizationService, wants_chart

log = get_logger(__name__)


class StreamingChatService:
    def __init__(
        self,
        make_retriever: RetrieverFactory,
        chat_model: BaseChatModel,
        web_search: WebSearch | None,
        sessionmaker: async_sessionmaker,
        generator: TextGenerator,
    ) -> None:
        self._make_retriever = make_retriever
        self._model = chat_model
        self._web = web_search
        self._sessionmaker = sessionmaker
        self._viz = VisualizationService(generator)

    async def stream(
        self,
        conversation_id: uuid.UUID,
        message: str,
        *,
        collection: str | None,
        thinking: bool = False,
    ) -> AsyncIterator[dict]:
        evidence: list[EvidenceItem] = []
        tools: list[str] = []  # tool names the agent invoked this turn
        settings = get_settings()

        # --- Input guardrail: refuse empty / over-long / prompt-injection before hitting the LLM.
        if settings.guardrails_enabled:
            check = check_input(message, max_chars=settings.max_input_chars)
            if not check.allowed:
                reason_key = (check.reason or "unknown").split(":", 1)[0]
                guardrail_blocks_total.labels(reason_key).inc()
                log.warning("guardrail_blocked_input", reason=check.reason)
                refusal = refusal_message(check.reason or "")
                yield {"type": "token", "token": refusal}
                yield {"type": "citations", "citations": []}
                yield {"type": "tools", "tools": []}
                async with self._sessionmaker() as session:
                    repo = ConversationRepository(session)
                    await repo.add_message(conversation_id, role="user", content=message)
                    await repo.add_message(conversation_id, role="assistant", content=refusal)
                    await session.commit()
                yield {"type": "done"}
                return
            if check.pii_types:
                log.info("guardrail_redacted_pii", types=check.pii_types)
            message = check.sanitized  # downstream uses the PII-redacted text

        # Retrieval is best-effort: a transient failure (e.g. embedding rate limit) should not
        # blank out the chat — we just answer with whatever evidence we have (possibly none).
        try:
            retriever = self._make_retriever(collection)
            if retriever is not None:
                tools.append("rag_search")
                chunks = await retriever.retrieve(message)
                evidence += [
                    EvidenceItem(
                        content=c.content,
                        document_id=c.document_id,
                        document_title=c.document_title,
                        page=c.page,
                        url=c.cloudinary_url,
                        source="documents",
                    )
                    for c in chunks
                ]
            # No topic attached → fall back to live web research.
            if collection is None and self._web is not None:
                tools.append("web_search")
                evidence += list(await self._web.search(message))
        except Exception:  # noqa: BLE001
            pass

        yield {"type": "evidence", "count": len(evidence)}
        evidence_str = format_evidence(evidence)

        if thinking:
            try:
                prompt = prompts.THINKING.format(question=message, evidence=evidence_str)
                async for token in stream_chat(self._model, prompt):
                    yield {"type": "thinking", "token": token}
            except Exception:  # noqa: BLE001 - thinking is best-effort
                pass

        parts: list[str] = []
        try:
            prompt = prompts.STREAM_ANSWER.format(question=message, evidence=evidence_str)
            async for token in stream_chat(self._model, prompt):
                parts.append(token)
                yield {"type": "token", "token": token}
        except Exception as exc:  # noqa: BLE001 - surface a friendly message to the UI
            detail = str(exc)
            fallback = (
                "The model is rate-limited right now (Gemini free tier) — please try again shortly."
                if "429" in detail or "RESOURCE_EXHAUSTED" in detail
                else "Sorry — something went wrong generating the answer. Please try again."
            )
            parts.append(fallback)
            yield {"type": "token", "token": fallback}

        answer = "".join(parts).strip()
        if not answer:
            answer = "I didn't get a response this time — please try again."
            yield {"type": "token", "token": answer}

        # --- Output guardrail: append a not-financial-advice disclaimer to investment-style answers.
        if settings.guardrails_enabled:
            with_disclaimer = apply_output_disclaimer(answer)
            if with_disclaimer != answer:
                yield {"type": "token", "token": with_disclaimer[len(answer) :]}
                answer = with_disclaimer

        citations = [dict(c) for c in build_citations(evidence)]
        yield {"type": "citations", "citations": citations}

        # Visualization agent: draw charts when the user asked to analyse / show / compare.
        charts: list[dict] = []
        if wants_chart(message):
            charts = await self._viz.build_charts(message, f"{answer}\n\n{evidence_str}")
            if charts:
                tools.append("chart")
            for chart in charts:
                yield {"type": "chart", "chart": chart}

        yield {"type": "tools", "tools": tools}

        async with self._sessionmaker() as session:
            repo = ConversationRepository(session)
            await repo.add_message(conversation_id, role="user", content=message)
            await repo.add_message(
                conversation_id,
                role="assistant",
                content=answer,
                citations=citations,
                charts=charts or None,
                tools=tools or None,
            )
            await session.commit()

        yield {"type": "done"}
