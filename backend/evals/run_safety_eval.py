"""Run the adversarial safety evaluation against the input guardrails (offline).

    python -m evals.run_safety_eval

Reports the block rate on injection attempts (recall), the false-positive rate on benign
questions, and PII redaction coverage. No model or network calls — pure guardrail logic.
"""

from app.core.guardrails import check_input
from evals.safety_dataset import SAFETY_SET


def main() -> None:
    injection_total = injection_blocked = 0
    benign_total = benign_blocked = 0
    pii_total = pii_redacted = 0
    rows: list[str] = []

    for case in SAFETY_SET:
        result = check_input(case["prompt"])
        blocked = not result.allowed
        expected = case["should_block"]
        ok = blocked == expected
        rows.append(
            f"[{'PASS' if ok else 'FAIL'}] {case['category']:9} "
            f"blocked={blocked!s:5} expected={expected!s:5}  {case['prompt'][:48]}"
        )

        if case["category"] == "injection":
            injection_total += 1
            injection_blocked += int(blocked)
        elif case["category"] == "benign":
            benign_total += 1
            benign_blocked += int(blocked)
        elif case["category"] == "pii":
            pii_total += 1
            pii_redacted += int(bool(result.pii_types))

    print("\n".join(rows))
    print("\n=== Safety metrics ===")
    print(f"Injection block rate (recall):   {injection_blocked}/{injection_total}")
    print(f"Benign false-positive rate:      {benign_blocked}/{benign_total}")
    print(f"PII redaction coverage:          {pii_redacted}/{pii_total}")


if __name__ == "__main__":
    main()
