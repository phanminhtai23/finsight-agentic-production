"""Task status endpoint."""

import uuid

from fastapi import APIRouter, HTTPException

from app.api.deps import TaskRepoDep
from app.schemas.task import TaskOut

router = APIRouter()


@router.get("/{task_id}", response_model=TaskOut)
async def get_task(task_id: uuid.UUID, task_repo: TaskRepoDep) -> TaskOut:
    task = await task_repo.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskOut.model_validate(task)
