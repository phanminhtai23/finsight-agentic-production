"""Safety guardrails for user input and model output.

Production hardening (Project 3). A thin, dependency-free safety layer that runs *before* a
prompt reaches the LLM and *after* the answer is produced:

* **Input validation** — length bounds (abuse / cost control) and empty-input rejection.
* **Prompt-injection defense** — heuristics for the common "ignore your instructions / reveal
  your system prompt / act as …" jailbreak patterns. Flagged input is refused, not forwarded.
* **PII redaction** — masks emails, phone numbers, credit-card and SSN-like numbers so sensitive
  data never lands in logs or traces.
* **Output disclaimer** — ensures investment-style answers carry a not-financial-advice notice.

The checks are intentionally heuristic and fast; they reduce risk without a heavyweight model.
"""

import re
from dataclasses import dataclass, field

# --- Prompt-injection heuristics -------------------------------------------------------------
# Matched case-insensitively against the raw user message. Kept conservative to avoid blocking
# legitimate financial questions.
_INJECTION_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(p, re.IGNORECASE)
    for p in (
        r"ignore\s+(all\s+|the\s+|your\s+)?(previous|prior|above|earlier)\s+(instructions?|prompts?|messages?)",
        r"disregard\s+(all\s+|the\s+|your\s+)?(previous|prior|above)\s+",
        r"forget\s+(everything|all|your)\s+(you|instructions|rules)",
        r"reveal\s+(your\s+)?(system\s+)?(prompt|instructions)",
        r"(show|print|repeat|reveal)\s+(me\s+)?(your\s+)?(system\s+prompt|initial\s+instructions)",
        r"you\s+are\s+now\s+(a|an|the|in)\b",
        r"act\s+as\s+(if\s+you\s+are\s+)?(a\s+|an\s+)?(dan|jailbroken|unfiltered|developer\s+mode)",
        r"developer\s+mode\s+(enabled|on)",
        r"bypass\s+(your\s+)?(safety|guidelines|filters|restrictions)",
        r"\bdo\s+anything\s+now\b",
    )
)

# --- PII patterns ----------------------------------------------------------------------------
_PII_PATTERNS: dict[str, re.Pattern[str]] = {
    "email": re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"),
    "credit_card": re.compile(r"\b(?:\d[ -]?){13,16}\b"),
    "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "phone": re.compile(r"\b(?:\+?\d{1,3}[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b"),
}

_DISCLAIMER = (
    "\n\n_Disclaimer: This is AI-generated research for informational purposes only and is "
    "not financial advice. Always verify figures against primary sources and consult a "
    "licensed professional before investing._"
)

# Heuristic: only append the disclaimer when the answer reads like investment guidance.
_ADVICE_MARKERS = re.compile(
    r"\b(invest|buy|sell|hold|undervalued|overvalued|recommend|portfolio|bullish|bearish|"
    r"price target|valuation|outperform|underperform)\b",
    re.IGNORECASE,
)


@dataclass
class GuardrailResult:
    """Outcome of an input check. ``allowed=False`` means the request must be refused."""

    allowed: bool
    reason: str | None = None
    sanitized: str = ""
    pii_types: list[str] = field(default_factory=list)


def detect_injection(text: str) -> str | None:
    """Return the matched injection phrase if the text looks like a prompt-injection attempt."""
    for pattern in _INJECTION_PATTERNS:
        match = pattern.search(text)
        if match:
            return match.group(0)
    return None


def redact_pii(text: str) -> tuple[str, list[str]]:
    """Replace PII with ``[REDACTED_<type>]`` markers. Returns (redacted_text, types_found)."""
    found: list[str] = []
    redacted = text
    for label, pattern in _PII_PATTERNS.items():
        if pattern.search(redacted):
            found.append(label)
            redacted = pattern.sub(f"[REDACTED_{label.upper()}]", redacted)
    return redacted, found


def check_input(text: str, *, max_chars: int = 8000) -> GuardrailResult:
    """Validate a user message before it reaches the model.

    Rejects empty or over-long input and likely prompt-injection attempts; otherwise returns the
    (PII-redacted) text to use downstream.
    """
    stripped = (text or "").strip()
    if not stripped:
        return GuardrailResult(allowed=False, reason="empty_input")
    if len(stripped) > max_chars:
        return GuardrailResult(
            allowed=False,
            reason=f"input_too_long: {len(stripped)} > {max_chars} characters",
        )

    injection = detect_injection(stripped)
    if injection:
        return GuardrailResult(allowed=False, reason=f"prompt_injection: {injection!r}")

    sanitized, pii = redact_pii(stripped)
    return GuardrailResult(allowed=True, sanitized=sanitized, pii_types=pii)


def apply_output_disclaimer(answer: str) -> str:
    """Append a not-financial-advice disclaimer when the answer reads like investment guidance."""
    if not answer:
        return answer
    if _ADVICE_MARKERS.search(answer) and "not financial advice" not in answer.lower():
        return answer + _DISCLAIMER
    return answer


# User-facing refusal messages keyed by guardrail reason prefix.
REFUSAL_MESSAGES = {
    "empty_input": "Please enter a question.",
    "input_too_long": ("Your message is too long. Please shorten it and try again."),
    "prompt_injection": (
        "I can't help with that request. I'm a financial research assistant — "
        "ask me about companies, filings or the documents you've uploaded."
    ),
}


def refusal_message(reason: str) -> str:
    """Map a guardrail ``reason`` to a friendly, user-facing refusal string."""
    key = reason.split(":", 1)[0]
    return REFUSAL_MESSAGES.get(
        key, "I can't help with that request. Please try rephrasing your question."
    )
