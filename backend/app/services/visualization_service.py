"""Visualization agent — turns financial data into chart specs the frontend renders.

Each chart "type" (bar, line, area, pie) is a tool the agent can pick from based on the data
and the user's request. Charts are produced only when the user asks to analyse / show / compare
something, to keep latency and token usage down.
"""

import json
import re

from app.rag.ports import TextGenerator

_ALLOWED = {"bar", "line", "area", "pie"}

_TRIGGER = re.compile(
    r"\b(analy|chart|graph|plot|visuali|diagram|show|compare|comparison|trend|breakdown|"
    r"distribution|over time|phân tích|biểu đồ|vẽ|so sánh|xu hướng|thống kê)\b",
    re.IGNORECASE,
)

_PROMPT = """You are FinSight's Visualization agent. Turn the data below into chart specs the UI
will render. Decide if one or more charts genuinely help; if not, output [].

Pick the right chart type (your tools):
- "line" or "area": a metric changing over time / periods (trend).
- "bar": comparing categories or periods.
- "pie": parts of a whole (composition / breakdown).

Output ONLY a JSON array of 1-3 chart objects, each:
{{
  "type": "bar"|"line"|"area"|"pie",
  "title": "short title",
  // for bar/line/area:
  "x": "<category/period field name>",
  "series": [{{"key": "revenue", "name": "Revenue"}}],     // 1-3 numeric series
  "data": [{{"<x>": "Q1", "revenue": 1250}}],               // 2-8 rows, numbers only
  // for pie instead of x/series/data above:
  "nameKey": "label", "valueKey": "value",
  "data": [{{"label": "Cloud", "value": 60}}]
}}

Use ONLY numbers that appear in the data. No commentary. If nothing is chartable, output [].

Question: {question}

Data:
{context}

JSON:"""


def wants_chart(message: str) -> bool:
    return bool(_TRIGGER.search(message or ""))


def _clean(raw: str) -> str:
    raw = raw.strip()
    raw = re.sub(r"^```(json)?", "", raw).strip()
    raw = re.sub(r"```$", "", raw).strip()
    start, end = raw.find("["), raw.rfind("]")
    return raw[start : end + 1] if start != -1 and end != -1 else raw


def _valid(chart: object) -> bool:
    return (
        isinstance(chart, dict)
        and chart.get("type") in _ALLOWED
        and isinstance(chart.get("data"), list)
        and len(chart["data"]) >= 2
    )


class VisualizationService:
    def __init__(self, generator: TextGenerator) -> None:
        self._gen = generator

    async def build_charts(self, question: str, context: str) -> list[dict]:
        try:
            raw = await self._gen.generate(_PROMPT.format(question=question, context=context))
            parsed = json.loads(_clean(raw))
        except Exception:  # noqa: BLE001 - charts are best-effort
            return []
        if not isinstance(parsed, list):
            return []
        return [c for c in parsed if _valid(c)][:3]
