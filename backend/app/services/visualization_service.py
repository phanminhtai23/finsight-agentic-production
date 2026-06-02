"""Visualization agent — turns financial data into chart specs the frontend renders.

Each chart "type" (bar, line, area, pie) is a tool the agent can pick from based on the data
and the user's request. Charts are produced only when the user asks to analyse / show / compare
something, to keep latency and token usage down.
"""

import json
import re

from app.rag.ports import TextGenerator

_ALLOWED = {
    "bar",
    "column",
    "line",
    "area",
    "pie",
    "donut",
    "radar",
    "rose",
    "scatter",
    "funnel",
}

_TRIGGER = re.compile(
    r"\b(analy|chart|graph|plot|visuali|diagram|show|compare|comparison|trend|breakdown|"
    r"distribution|over time|phân tích|biểu đồ|vẽ|so sánh|xu hướng|thống kê)\b",
    re.IGNORECASE,
)

_PROMPT = """You are FinSight's Visualization agent (powered by the AntV chart library). Turn the
data below into beautiful, well-chosen chart specs the UI renders. Decide if one or more charts
genuinely help; if not, output [].

Pick the BEST chart type for the data (your toolbox):
- "line": a metric changing over time / periods (trend). Use 1-3 series to compare trends.
- "area": a trend where magnitude/accumulation matters; good for stacked composition over time.
- "column": compare values across categories or periods (vertical bars). Multiple series = grouped.
- "bar": same as column but horizontal — better for many/long category labels.
- "pie" / "donut": parts of a whole (composition / breakdown). Prefer "donut" — it's cleaner.
- "rose": a nightingale/rose chart for cyclical or ranked categorical magnitudes.
- "radar": compare ONE entity across several metrics, or a few entities across shared metrics.
- "scatter": relationship between two numeric measures.
- "funnel": stages that decrease in sequence (e.g. pipeline / conversion).

Prefer variety and the most insightful view; avoid defaulting everything to a plain bar chart.

Output ONLY a JSON array of 1-3 chart objects, each:
{{
  "type": "column"|"bar"|"line"|"area"|"pie"|"donut"|"radar"|"rose"|"scatter"|"funnel",
  "title": "short, specific title",
  // for column/bar/line/area/radar/scatter:
  "x": "<category/period field name>",
  "series": [{{"key": "revenue", "name": "Revenue"}}],     // 1-3 numeric series
  "data": [{{"<x>": "Q1", "revenue": 1250}}],               // 2-8 rows, numbers only
  "stack": false,                                            // optional: stacked area/column
  // for pie/donut/rose/funnel instead of x/series:
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
