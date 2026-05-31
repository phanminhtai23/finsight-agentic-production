"""Skill abstraction.

A *skill* is a small, self-contained, reusable capability (a prompt + how to run it) that any
agent or endpoint can invoke. Skills depend on the ``TextGenerator`` port, not a concrete LLM.
"""

from typing import Protocol, runtime_checkable

from app.rag.ports import TextGenerator


@runtime_checkable
class Skill(Protocol):
    name: str
    description: str

    async def run(self, generator: TextGenerator, **kwargs: str) -> str: ...


class PromptSkill:
    """Base skill that formats a template with kwargs and runs it through the generator."""

    name: str = ""
    description: str = ""
    template: str = "{input}"

    async def run(self, generator: TextGenerator, **kwargs: str) -> str:
        prompt = self.template.format(**kwargs)
        return (await generator.generate(prompt)).strip()


class SkillError(KeyError):
    pass


class SkillRegistry:
    def __init__(self, skills: list[Skill]) -> None:
        self._skills: dict[str, Skill] = {s.name: s for s in skills}

    def get(self, name: str) -> Skill:
        try:
            return self._skills[name]
        except KeyError as exc:
            raise SkillError(f"Unknown skill: {name}") from exc

    def list(self) -> list[Skill]:
        return list(self._skills.values())
