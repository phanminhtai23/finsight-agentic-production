"""Agent node implementations for the multi-agent graph.

Each node is a small, single-responsibility step that reads and returns a partial
``AgentState``. Collaborators (retriever, LLM, web search) are injected.
"""

from collections.abc import Callable

from app.agents import prompts
from app.agents.state import AgentState, CitationItem, EvidenceItem
from app.agents.web import NullWebSearch, WebSearch
from app.rag.ports import TextGenerator
from app.rag.retrieval.hybrid import HybridRetriever

# Given a topic's collection name (or None), return a retriever for it (or None to skip RAG).
RetrieverFactory = Callable[[str | None], HybridRetriever | None]

_SNIPPET = 240


def format_evidence(evidence: list[EvidenceItem]) -> str:
    if not evidence:
        return "(no evidence found)"
    blocks = []
    for i, e in enumerate(evidence, start=1):
        loc = f" (p.{e['page']})" if e.get("page") else ""
        title = e.get("document_title") or e.get("url") or e.get("document_id") or "source"
        blocks.append(f"[{i}] {title}{loc}:\n{e.get('content', '')}")
    return "\n\n".join(blocks)


def build_citations(evidence: list[EvidenceItem]) -> list[CitationItem]:
    citations: list[CitationItem] = []
    for i, e in enumerate(evidence, start=1):
        snippet = (e.get("content") or "").strip().replace("\n", " ")
        if len(snippet) > _SNIPPET:
            snippet = snippet[:_SNIPPET].rstrip() + "…"
        citations.append(
            CitationItem(
                index=i,
                document_id=e.get("document_id", ""),
                document_title=e.get("document_title"),
                page=e.get("page"),
                url=e.get("url"),
                snippet=snippet,
            )
        )
    return citations


class FinSightAgents:
    def __init__(
        self,
        make_retriever: RetrieverFactory,
        generator: TextGenerator,
        web_search: WebSearch | None = None,
        *,
        max_revisions: int = 2,
    ) -> None:
        self._make_retriever = make_retriever
        self._gen = generator
        self._web = web_search or NullWebSearch()
        self._max_revisions = max_revisions

    async def supervisor(self, state: AgentState) -> dict:
        verdict = (
            await self._gen.generate(prompts.SUPERVISOR.format(question=state["question"]))
        ).lower()
        needs_web = "needs_web: yes" in verdict or "needs_web:yes" in verdict
        return {"needs_web": needs_web, "revisions": state.get("revisions", 0)}

    async def retrieval(self, state: AgentState) -> dict:
        retriever = self._make_retriever(state.get("collection"))
        if retriever is None:
            return {}  # conversation has no topic/data attached → skip document RAG
        chunks = await retriever.retrieve(state["question"])
        found = [
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
        return {"evidence": (state.get("evidence") or []) + found}

    async def market_research(self, state: AgentState) -> dict:
        found = await self._web.search(state["question"])
        return {"evidence": (state.get("evidence") or []) + list(found)}

    async def analyst(self, state: AgentState) -> dict:
        evidence = format_evidence(state.get("evidence") or [])
        analysis = await self._gen.generate(
            prompts.ANALYST.format(question=state["question"], evidence=evidence)
        )
        return {"analysis": analysis.strip()}

    async def writer(self, state: AgentState) -> dict:
        evidence_list = state.get("evidence") or []
        answer = await self._gen.generate(
            prompts.WRITER.format(
                question=state["question"],
                analysis=state.get("analysis", ""),
                evidence=format_evidence(evidence_list),
            )
        )
        return {"answer": answer.strip(), "citations": build_citations(evidence_list)}

    async def critic(self, state: AgentState) -> dict:
        verdict = (
            await self._gen.generate(
                prompts.CRITIC.format(
                    question=state["question"],
                    evidence=format_evidence(state.get("evidence") or []),
                    answer=state.get("answer", ""),
                )
            )
        ).strip()
        approved = verdict.upper().startswith("APPROVED")
        revisions = state.get("revisions", 0) + (0 if approved else 1)
        return {"approved": approved, "critique": verdict, "revisions": revisions}

    # --- routing ---
    def route_after_retrieval(self, state: AgentState) -> str:
        return "market_research" if state.get("needs_web") else "analyst"

    def route_after_critic(self, state: AgentState) -> str:
        if state.get("approved") or state.get("revisions", 0) >= self._max_revisions:
            return "end"
        return "analyst"
