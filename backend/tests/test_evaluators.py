"""Unit tests for eval metrics (pure parts)."""

from evals.evaluators import expected_recall, has_citations


def test_has_citations():
    assert has_citations("Revenue was $1,250M [1].")
    assert not has_citations("Revenue was $1,250M.")
    assert not has_citations("")


def test_expected_recall():
    answer = "Net revenue was $1,250 million with a 32% gross margin."
    assert expected_recall(answer, ["1,250", "32%"]) == 1.0
    assert expected_recall(answer, ["1,250", "999"]) == 0.5
    assert expected_recall(answer, []) == 1.0
    assert expected_recall("", ["1,250"]) == 0.0
