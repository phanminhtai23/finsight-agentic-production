"""Skill DTOs."""

from pydantic import BaseModel


class SkillInfo(BaseModel):
    name: str
    description: str


class SkillRunRequest(BaseModel):
    args: dict[str, str]


class SkillRunResponse(BaseModel):
    name: str
    output: str
