"""Evaluation metrics for FinSight answers.

The heuristic metrics are pure and unit-tested; the LLM-judge groundedness check takes a
``TextGenerator`` so it can be driven by Gemini (or a fake in tests).
"""

import re

from app.rag.ports import TextGenerator

_CITATION_RE = re.compile(r"\[\d+\]")

_GROUNDED_PROMPT = """You are grading whether an ANSWER is grounded in the EVIDENCE.
Reply with a single number 1 (fully grounded), 0.5 (partly), or 0 (not grounded). Nothing else.

QUESTION: {question}
EVIDENCE:
{evidence}
ANSWER:
{answer}

Score:"""


def has_citations(answer: str) -> bool:
    """True if the answer contains at least one [n] citation marker."""
    return bool(_CITATION_RE.search(answer or ""))


def expected_recall(answer: str, expected: list[str]) -> float:
    """Fraction of expected substrings present in the answer (case-insensitive)."""
    if not expected:
        return 1.0
    lowered = (answer or "").lower()
    hits = sum(1 for e in expected if e.lower() in lowered)
    return hits / len(expected)


async def groundedness(
    generator: TextGenerator, *, question: str, answer: str, evidence: str
) -> float:
    """LLM-as-judge: is the answer supported by the evidence? Returns 0 / 0.5 / 1."""
    raw = await generator.generate(
        _GROUNDED_PROMPT.format(question=question, evidence=evidence, answer=answer)
    )
    match = re.search(r"(1(\.0)?|0\.5|0)", raw.strip())
    return float(match.group(1)) if match else 0.0
