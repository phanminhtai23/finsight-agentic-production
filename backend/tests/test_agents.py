"""Unit test for the multi-agent graph using fakes (no LLM/DB/checkpointer)."""

from app.agents.graph import build_graph
from app.rag.retrieval.models import RetrievedChunk


class FakeRetriever:
    async def retrieve(self, query, *, document_ids=None, user_id=None):
        return [
            RetrievedChunk(
                chunk_id="1",
                content="Net revenue was $1,250 million, up 18% YoY.",
                score=1.0,
                document_id="doc",
                document_title="Q3.pdf",
                page=1,
            )
        ]


class FakeGen:
    """Canned responses keyed on each prompt's distinctive text."""

    async def generate(self, prompt: str) -> str:
        if "NEEDS_WEB:" in prompt:
            return "NEEDS_WEB: no"
        if "reply exactly: APPROVED" in prompt:
            return "APPROVED"
        if "Analysis notes:" in prompt:
            return "Net revenue $1,250M, +18% YoY [1]."
        if "Final answer" in prompt:
            return "Net revenue was $1,250 million, up 18% YoY [1]."
        return "ok"


async def test_graph_produces_cited_answer():
    graph = build_graph(lambda _c: FakeRetriever(), FakeGen())
    result = await graph.ainvoke(
        {"question": "What was revenue?", "messages": [], "collection": "t"}
    )

    assert "[1]" in result["answer"]
    assert result["approved"] is True
    assert result["citations"][0]["index"] == 1
    assert result["citations"][0]["document_title"] == "Q3.pdf"
    assert result["citations"][0]["page"] == 1


async def test_graph_routes_to_web_when_needed():
    """When the supervisor says NEEDS_WEB: yes, the market_research node runs."""
    calls = {"web": 0}

    class WebSearch:
        async def search(self, query, *, k=5):
            calls["web"] += 1
            return [{"content": "Live price 100", "url": "http://x", "source": "web"}]

    class WebGen(FakeGen):
        async def generate(self, prompt: str) -> str:
            if "NEEDS_WEB:" in prompt:
                return "NEEDS_WEB: yes"
            return await super().generate(prompt)

    graph = build_graph(lambda _c: FakeRetriever(), WebGen(), WebSearch())
    await graph.ainvoke({"question": "current stock price?", "messages": [], "collection": "t"})
    assert calls["web"] == 1
