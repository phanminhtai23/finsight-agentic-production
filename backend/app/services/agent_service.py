"""Agent service — runs the multi-agent graph for a conversation thread."""

import uuid

from langchain_core.messages import HumanMessage

from app.agents.state import CitationItem
from app.repositories.conversation_repository import ConversationRepository


class AgentService:
    def __init__(self, graph: object, conversation_repo: ConversationRepository) -> None:
        self._graph = graph
        self._conversations = conversation_repo

    async def chat(
        self,
        conversation_id: uuid.UUID,
        message: str,
        *,
        collection: str | None = None,
    ) -> tuple[str, list[CitationItem]]:
        # Reset per-turn transient fields; ``messages`` is appended via its reducer.
        initial = {
            "messages": [HumanMessage(content=message)],
            "question": message,
            "collection": collection,
            "evidence": [],
            "analysis": "",
            "answer": "",
            "citations": [],
            "approved": False,
            "revisions": 0,
            "needs_web": False,
        }
        config = {"configurable": {"thread_id": str(conversation_id)}}
        result = await self._graph.ainvoke(initial, config=config)

        answer = result.get("answer", "")
        citations = result.get("citations", [])

        await self._conversations.add_message(conversation_id, role="user", content=message)
        await self._conversations.add_message(
            conversation_id, role="assistant", content=answer, citations=list(citations)
        )
        return answer, citations
