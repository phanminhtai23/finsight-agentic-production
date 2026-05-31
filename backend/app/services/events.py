"""Redis pub/sub for streaming background-task progress to WebSocket clients.

Publishing progress here (rather than holding a request open) is what lets the user keep
chatting while ingestion / research runs in a worker.
"""

import json

import redis.asyncio as redis


def task_channel(task_id: str) -> str:
    return f"task:{task_id}"


class EventPublisher:
    def __init__(self, client: redis.Redis) -> None:
        self._client = client

    async def publish_task(
        self,
        task_id: str,
        *,
        status: str,
        progress: int,
        message: str | None = None,
        result: dict | None = None,
    ) -> None:
        payload = json.dumps(
            {
                "task_id": task_id,
                "status": status,
                "progress": progress,
                "message": message,
                "result": result,
            }
        )
        await self._client.publish(task_channel(task_id), payload)
