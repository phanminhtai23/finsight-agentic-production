"""RAG question-answering with grounded citations.

This is the single-shot RAG path (retrieve → answer with [n] citations). The full
multi-agent graph (Supervisor/Analyst/Critic/...) builds on the same retriever in M2.
"""

import uuid
from dataclasses import dataclass

from app.rag.ports import TextGenerator
from app.rag.retrieval.citation import Citation, build_citations
from app.rag.retrieval.hybrid import HybridRetriever
from app.rag.retrieval.models import RetrievedChunk

_SYSTEM = """You are FinSight, a financial research assistant. Answer the question using ONLY
the numbered evidence below. Cite every factual claim with its evidence number like [1], [2].
If the evidence is insufficient, say so plainly. Be concise and precise with figures.

Question:
{question}

Evidence:
{evidence}

Answer (with inline [n] citations):"""


def _format_evidence(chunks: list[RetrievedChunk]) -> str:
    blocks = []
    for i, chunk in enumerate(chunks, start=1):
        loc = f" (p.{chunk.page})" if chunk.page is not None else ""
        title = chunk.document_title or chunk.document_id
        blocks.append(f"[{i}] {title}{loc}:\n{chunk.content}")
    return "\n\n".join(blocks)


@dataclass
class AnswerResult:
    answer: str
    citations: list[Citation]


class QAService:
    def __init__(self, retriever: HybridRetriever, generator: TextGenerator) -> None:
        self._retriever = retriever
        self._generator = generator

    async def answer(
        self,
        question: str,
        *,
        document_ids: list[uuid.UUID] | None = None,
        user_id: uuid.UUID | None = None,
    ) -> AnswerResult:
        evidence = await self._retriever.retrieve(
            question, document_ids=document_ids, user_id=user_id
        )
        if not evidence:
            return AnswerResult(
                answer="I couldn't find relevant information in the available documents.",
                citations=[],
            )
        prompt = _SYSTEM.format(question=question, evidence=_format_evidence(evidence))
        answer = await self._generator.generate(prompt)
        return AnswerResult(answer=answer.strip(), citations=build_citations(evidence))
