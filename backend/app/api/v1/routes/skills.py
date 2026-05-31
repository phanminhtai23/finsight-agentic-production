"""Skill endpoints — list and invoke reusable capabilities."""

from fastapi import APIRouter, HTTPException

from app.api.deps import SkillRegistryDep
from app.core.llm import get_text_generator
from app.schemas.skill import SkillInfo, SkillRunRequest, SkillRunResponse
from app.skills.base import SkillError

router = APIRouter()


@router.get("", response_model=list[SkillInfo])
def list_skills(registry: SkillRegistryDep) -> list[SkillInfo]:
    return [SkillInfo(name=s.name, description=s.description) for s in registry.list()]


@router.post("/{name}", response_model=SkillRunResponse)
async def run_skill(
    name: str, body: SkillRunRequest, registry: SkillRegistryDep
) -> SkillRunResponse:
    try:
        skill = registry.get(name)
    except SkillError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    try:
        output = await skill.run(get_text_generator(), **body.args)
    except KeyError as exc:
        raise HTTPException(status_code=422, detail=f"Missing argument: {exc}") from exc
    return SkillRunResponse(name=name, output=output)
