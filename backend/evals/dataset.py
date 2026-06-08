"""Evaluation dataset for the bundled sample document (Nimbus Cloud Inc. FY2024).

Each record in :data:`EVAL_SET` is a question / expected-answer pair used by
:mod:`evals.run_eval` to measure the RAG pipeline's recall against a
known-good financial report (*samples/sample_financial_report.docx*).

Schema
------
Each entry is an :class:`EvalCase` with:

* ``question`` (``str``) — natural-language question sent to the agent.
* ``expected`` (``list[str]``) — one or more substrings that **must all
  appear** in a correct answer (case-insensitive exact-string match).

Usage
-----
Prefer the validated accessor over importing the raw list directly::

    from evals.dataset import get_eval_set
    for case in get_eval_set():
        response = run_agent(case["question"])
        hits = [e for e in case["expected"] if e in response]
        ...

The raw :data:`EVAL_SET` constant is kept for backwards compatibility with
code that imports it directly.
"""

from __future__ import annotations

from typing import TypedDict


class EvalCase(TypedDict):
    """A single question / expected-answer pair for RAG evaluation."""

    question: str
    """Natural-language question sent to the agent under evaluation."""

    expected: list[str]
    """Substrings that must all appear in a correct answer (case-insensitive)."""


_EVAL_SET: list[EvalCase] = [
    {
        "question": "What was Nimbus Cloud Inc.'s Q4 2024 revenue?",
        "expected": ["1,180"],
    },
    {
        "question": "What was Nimbus Cloud's gross margin in Q4 2024?",
        "expected": ["32%"],
    },
    {
        "question": "What was Nimbus Cloud's net income in Q4 2024?",
        "expected": ["262"],
    },
    {
        "question": "How much cash and total debt did Nimbus Cloud have at year end?",
        "expected": ["2,100", "900"],
    },
    {
        "question": "What full-year 2024 revenue growth does Nimbus Cloud management expect?",
        "expected": ["16%"],
    },
]


def get_eval_set() -> list[EvalCase]:
    """Return the validated evaluation dataset.

    Performs basic integrity checks on every entry before returning the list
    so that malformed records are caught early — at import time during a CI
    run — rather than mid-evaluation.

    Returns
    -------
    list[EvalCase]
        A copy of the validated evaluation dataset.

    Raises
    ------
    ValueError
        If any entry is missing required keys, has an empty ``question``, or
        has an empty ``expected`` list.

    Examples
    --------
    >>> cases = get_eval_set()
    >>> len(cases) > 0
    True
    >>> all("question" in c and "expected" in c for c in cases)
    True
    """
    required_keys = {"question", "expected"}
    errors: list[str] = []

    for i, case in enumerate(_EVAL_SET):
        missing = required_keys - case.keys()
        if missing:
            errors.append(f"EVAL_SET[{i}]: missing keys {sorted(missing)}")
            continue
        if not case["question"].strip():
            errors.append(f"EVAL_SET[{i}]: 'question' must not be empty")
        if not case["expected"]:
            errors.append(f"EVAL_SET[{i}]: 'expected' list must not be empty")
        if any(not isinstance(e, str) or not e.strip() for e in case["expected"]):
            errors.append(f"EVAL_SET[{i}]: all 'expected' entries must be non-empty strings")

    if errors:
        raise ValueError("Evaluation dataset has invalid entries:\n" + "\n".join(errors))

    return list(_EVAL_SET)


# Backwards-compatibility alias — existing callers that import EVAL_SET directly
# continue to work; new code should use get_eval_set() for validated access.
EVAL_SET = _EVAL_SET
