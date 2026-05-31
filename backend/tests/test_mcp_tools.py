"""Unit tests for MCP tool logic (pure parts)."""

import pytest

from app.agents.mcp_web import _parse_tool_result
from mcp_server.tools import financial_calculator


def test_financial_calculator_basic():
    assert financial_calculator("2 + 3 * 4") == 14.0
    assert round(financial_calculator("(1250-1059)/1059*100"), 2) == 18.04


def test_financial_calculator_rejects_unsafe():
    with pytest.raises(ValueError):
        financial_calculator("__import__('os').system('ls')")
    with pytest.raises(ValueError):
        financial_calculator("abs(-1)")  # function calls are not allowed


def test_parse_tool_result_extracts_json():
    class Block:
        text = '[{"title": "T", "url": "http://x", "snippet": "s"}]'

    class Result:
        content = [Block()]

    parsed = _parse_tool_result(Result())
    assert parsed[0]["title"] == "T"


def test_parse_tool_result_empty_on_garbage():
    class Block:
        text = "not json"

    class Result:
        content = [Block()]

    assert _parse_tool_result(Result()) == []
