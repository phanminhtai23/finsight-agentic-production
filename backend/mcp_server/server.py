"""FinSight MCP server — exposes research/finance tools over the Model Context Protocol.

Run:  python -m mcp_server.server   (streamable-http on :8001, path /mcp)

Agents connect as MCP clients (see app/agents/mcp_web.py), satisfying the Ready Tensor
"MCP communication" criterion and providing >=3 tools.
"""

import json

from mcp.server.fastmcp import FastMCP

from mcp_server import tools

mcp = FastMCP("finsight-tools", host="0.0.0.0", port=8001)


@mcp.tool()
async def web_search(query: str, k: int = 5) -> str:
    """Search the web for up-to-date information. Returns JSON [{title,url,snippet}]."""
    return json.dumps(await tools.web_search(query, k))


@mcp.tool()
async def company_financials(company: str, k: int = 5) -> str:
    """Find a company's latest reported financials. Returns JSON [{title,url,snippet}]."""
    return json.dumps(await tools.company_financials(company, k))


@mcp.tool()
async def fetch_url(url: str, max_chars: int = 3000) -> str:
    """Fetch a URL and return its readable text content."""
    return await tools.fetch_url(url, max_chars)


@mcp.tool()
def financial_calculator(expression: str) -> str:
    """Safely evaluate an arithmetic expression, e.g. '(1250-1059)/1059*100'."""
    return str(tools.financial_calculator(expression))


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
