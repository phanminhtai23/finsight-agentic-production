"""Multi-agent graph assembly (LangGraph, supervisor-coordinated).

Flow:
    START → supervisor (triage: needs web?) → retrieval
          → [market_research if needs_web] → analyst → writer → critic
          → analyst (revise, bounded) | END

Compiled with a checkpointer so each conversation thread is durably persisted/resumable.
"""

from langgraph.graph import END, START, StateGraph

from app.agents.nodes import FinSightAgents, RetrieverFactory
from app.agents.state import AgentState
from app.agents.web import WebSearch
from app.rag.ports import TextGenerator

__all__ = ["AgentState", "build_graph"]


def build_graph(
    make_retriever: RetrieverFactory,
    generator: TextGenerator,
    web_search: WebSearch | None = None,
    *,
    checkpointer: object | None = None,
    max_revisions: int = 2,
):
    agents = FinSightAgents(make_retriever, generator, web_search, max_revisions=max_revisions)

    graph = StateGraph(AgentState)
    graph.add_node("supervisor", agents.supervisor)
    graph.add_node("retrieval", agents.retrieval)
    graph.add_node("market_research", agents.market_research)
    graph.add_node("analyst", agents.analyst)
    graph.add_node("writer", agents.writer)
    graph.add_node("critic", agents.critic)

    graph.add_edge(START, "supervisor")
    graph.add_edge("supervisor", "retrieval")
    graph.add_conditional_edges(
        "retrieval",
        agents.route_after_retrieval,
        {"market_research": "market_research", "analyst": "analyst"},
    )
    graph.add_edge("market_research", "analyst")
    graph.add_edge("analyst", "writer")
    graph.add_edge("writer", "critic")
    graph.add_conditional_edges(
        "critic", agents.route_after_critic, {"analyst": "analyst", "end": END}
    )

    return graph.compile(checkpointer=checkpointer)
