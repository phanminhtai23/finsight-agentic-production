"""Data access for background tasks."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task, TaskStatus, TaskType


class TaskRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        type: TaskType,
        conversation_id: uuid.UUID | None = None,
        input: dict | None = None,
    ) -> Task:
        task = Task(type=type, conversation_id=conversation_id, input=input)
        self.session.add(task)
        await self.session.flush()
        return task

    async def get(self, task_id: uuid.UUID) -> Task | None:
        return await self.session.get(Task, task_id)

    async def update(
        self,
        task_id: uuid.UUID,
        *,
        status: TaskStatus | None = None,
        progress: int | None = None,
        result: dict | None = None,
        error: str | None = None,
    ) -> Task | None:
        task = await self.session.get(Task, task_id)
        if task is None:
            return None
        if status is not None:
            task.status = status
        if progress is not None:
            task.progress = progress
        if result is not None:
            task.result = result
        if error is not None:
            task.error = error
        return task
