"""Tool abstractions.

Every capability the agents can call (RAG search, web search, calculator, ...) implements
this ``Tool`` protocol. Agents depend on the abstraction; concrete tools — including ones
proxied from the MCP server — are injected. Adding a new tool requires no change to agent
code (Open/Closed principle).
"""

from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel


class ToolResult(BaseModel):
    """Uniform tool output, including citation-ready source metadata."""

    output: Any
    sources: list[dict[str, Any]] = []


@runtime_checkable
class Tool(Protocol):
    name: str
    description: str

    async def run(self, **kwargs: Any) -> ToolResult: ...
