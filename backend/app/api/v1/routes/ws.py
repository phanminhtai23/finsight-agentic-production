"""WebSocket endpoint streaming background-task progress from Redis pub/sub."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.cache import create_redis_pool
from app.core.config import get_settings
from app.services.events import task_channel

router = APIRouter()


@router.websocket("/tasks/{task_id}")
async def task_progress_ws(websocket: WebSocket, task_id: str) -> None:
    """Forward progress events for a task to the client until it disconnects."""
    await websocket.accept()
    client = create_redis_pool(get_settings())
    pubsub = client.pubsub()
    await pubsub.subscribe(task_channel(task_id))
    try:
        async for message in pubsub.listen():
            if message.get("type") == "message":
                await websocket.send_text(message["data"])
    except WebSocketDisconnect:
        pass
    finally:
        await pubsub.unsubscribe(task_channel(task_id))
        await pubsub.aclose()
        await client.aclose()
