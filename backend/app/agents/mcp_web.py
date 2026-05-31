"""MCP-backed web search — the Market Research agent's WebSearch implementation.

Connects to the FinSight MCP server (streamable-http) and calls its ``web_search`` tool,
mapping results to evidence. This is the concrete MCP-client side of the system.
"""

import json

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from app.agents.state import EvidenceItem


def _parse_tool_result(result: object) -> list[dict]:
    for block in getattr(result, "content", []) or []:
        text = getattr(block, "text", None)
        if text:
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return []
    return []


class McpWebSearch:
    def __init__(self, url: str, *, tool: str = "web_search") -> None:
        self._url = url
        self._tool = tool

    async def search(self, query: str, *, k: int = 5) -> list[EvidenceItem]:
        try:
            async with (
                streamablehttp_client(self._url) as (read, write, _),
                ClientSession(read, write) as session,
            ):
                await session.initialize()
                result = await session.call_tool(self._tool, {"query": query, "k": k})
            hits = _parse_tool_result(result)
        except Exception:
            return []  # graceful: a research outage shouldn't break the chat

        return [
            EvidenceItem(
                content=hit.get("snippet") or "",
                document_id="web",
                document_title=hit.get("title"),
                page=None,
                url=hit.get("url"),
                source="web",
            )
            for hit in hits
            if hit.get("snippet")
        ]
