"""Unit tests for skills (fake generator)."""

import pytest

from app.skills.base import SkillError
from app.skills.library import SummarizeSkill, default_registry


class Gen:
    async def generate(self, prompt: str) -> str:
        return "  • point a\n• point b  "


async def test_summarize_runs_and_strips():
    out = await SummarizeSkill().run(Gen(), input="some long text")
    assert out == "• point a\n• point b"


def test_registry_lists_builtin_skills():
    names = {s.name for s in default_registry().list()}
    assert {"summarize", "translate", "fact_check"} <= names


def test_registry_unknown_raises():
    with pytest.raises(SkillError):
        default_registry().get("does_not_exist")
