"""Evaluation dataset for the bundled sample document (ACME Q3 2024)."""

EVAL_SET: list[dict] = [
    {
        "question": "What was ACME Corporation's Q3 2024 net revenue?",
        "expected": ["1,250"],
    },
    {
        "question": "What was ACME's gross margin in Q3 2024?",
        "expected": ["32%"],
    },
    {
        "question": "What was ACME's net income in Q3 2024?",
        "expected": ["180"],
    },
    {
        "question": "How much cash and total debt did ACME have at quarter end?",
        "expected": ["2,100", "900"],
    },
    {
        "question": "What full-year 2024 revenue growth does ACME management expect?",
        "expected": ["16%"],
    },
]
