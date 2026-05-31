"""CI regression gate: the guardrail must classify every adversarial safety case correctly."""

import pytest
from evals.safety_dataset import SAFETY_SET

from app.core.guardrails import check_input


@pytest.mark.parametrize("case", SAFETY_SET, ids=lambda c: c["category"] + ":" + c["prompt"][:24])
def test_guardrail_matches_expected(case: dict) -> None:
    result = check_input(case["prompt"])
    assert (not result.allowed) == case["should_block"], case["prompt"]


def test_injection_recall_is_total():
    injection = [c for c in SAFETY_SET if c["category"] == "injection"]
    blocked = [c for c in injection if not check_input(c["prompt"]).allowed]
    assert len(blocked) == len(injection), "every injection attempt must be blocked"


def test_no_false_positives_on_benign():
    benign = [c for c in SAFETY_SET if c["category"] == "benign"]
    allowed = [c for c in benign if check_input(c["prompt"]).allowed]
    assert len(allowed) == len(benign), "benign financial questions must not be blocked"
