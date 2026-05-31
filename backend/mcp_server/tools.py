"""Tool implementations exposed by the MCP server.

Kept free of MCP plumbing so the pure pieces (e.g. the calculator) are unit-testable and the
async tools can be reused directly.
"""

from __future__ import annotations

import ast
import asyncio
import operator
import re

import httpx

_ALLOWED_BINOPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.FloorDiv: operator.floordiv,
}
_ALLOWED_UNARY = {ast.UAdd: operator.pos, ast.USub: operator.neg}


def _eval_node(node: ast.AST) -> float:
    if isinstance(node, ast.Expression):
        return _eval_node(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_BINOPS:
        return _ALLOWED_BINOPS[type(node.op)](_eval_node(node.left), _eval_node(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_UNARY:
        return _ALLOWED_UNARY[type(node.op)](_eval_node(node.operand))
    raise ValueError("Unsupported or unsafe expression")


def financial_calculator(expression: str) -> float:
    """Safely evaluate an arithmetic expression (e.g. '(1250-1059)/1059*100')."""
    tree = ast.parse(expression, mode="eval")
    return _eval_node(tree)


async def web_search(query: str, k: int = 5) -> list[dict]:
    """Free web search via DuckDuckGo (no API key)."""

    def _do() -> list[dict]:
        from ddgs import DDGS

        with DDGS() as ddgs:
            hits = ddgs.text(query, max_results=k)
        return [
            {"title": h.get("title"), "url": h.get("href"), "snippet": h.get("body")} for h in hits
        ]

    try:
        return await asyncio.to_thread(_do)
    except Exception as exc:  # noqa: BLE001 - search is best-effort
        return [{"title": "search_error", "url": None, "snippet": str(exc)}]


async def company_financials(company: str, k: int = 5) -> list[dict]:
    """Focused web search for a company's latest reported financials."""
    return await web_search(f"{company} latest quarterly results revenue net income earnings", k=k)


async def fetch_url(url: str, max_chars: int = 3000) -> str:
    """Fetch a URL and return its readable text (tags stripped, truncated)."""
    try:
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": "FinSight/0.1"})
            resp.raise_for_status()
            text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", resp.text, flags=re.S | re.I)
            text = re.sub(r"<[^>]+>", " ", text)
            text = re.sub(r"\s+", " ", text).strip()
            return text[:max_chars]
    except Exception as exc:  # noqa: BLE001
        return f"fetch_error: {exc}"
