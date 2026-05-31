"""Conversation endpoints — create (optionally pinned to a topic) and chat via the graph."""

import json
import uuid

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.api.deps import (
    AgentServiceDep,
    ConversationRepoDep,
    CurrentUserDep,
    SessionDep,
    StreamingChatServiceDep,
    TopicRepoDep,
)
from app.schemas.conversation import (
    ChatRequest,
    ChatResponse,
    ConversationCreate,
    ConversationOut,
    MessageOut,
)
from app.schemas.qa import CitationOut

router = APIRouter()


def _short_title(text: str) -> str:
    """A short, clean title derived from the first message."""
    collapsed = " ".join(text.split())
    return f"{collapsed[:40].rstrip()}…" if len(collapsed) > 40 else collapsed


@router.post("", response_model=ConversationOut, status_code=201)
async def create_conversation(
    body: ConversationCreate,
    user: CurrentUserDep,
    repo: ConversationRepoDep,
    topic_repo: TopicRepoDep,
    session: SessionDep,
) -> ConversationOut:
    if body.topic_id is not None and await topic_repo.get_owned(body.topic_id, user.id) is None:
        raise HTTPException(status_code=404, detail="Topic not found")
    conversation = await repo.create(user_id=user.id, title=body.title, topic_id=body.topic_id)
    await session.commit()
    return ConversationOut.model_validate(conversation)


@router.get("", response_model=list[ConversationOut])
async def list_conversations(
    user: CurrentUserDep, repo: ConversationRepoDep
) -> list[ConversationOut]:
    return [ConversationOut.model_validate(c) for c in await repo.list_for_user(user.id)]


@router.post("/{conversation_id}/messages", response_model=ChatResponse)
async def post_message(
    conversation_id: uuid.UUID,
    body: ChatRequest,
    user: CurrentUserDep,
    repo: ConversationRepoDep,
    topic_repo: TopicRepoDep,
    agents: AgentServiceDep,
) -> ChatResponse:
    """Send a message; the multi-agent graph answers with grounded citations."""
    conversation = await repo.get(conversation_id)
    if conversation is None or conversation.user_id != user.id:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if not conversation.title:  # auto-name from the first message
        conversation.title = _short_title(body.message)

    collection: str | None = None
    if conversation.topic_id is not None:
        topic = await topic_repo.get(conversation.topic_id)
        collection = topic.qdrant_collection if topic else None

    answer, citations = await agents.chat(conversation_id, body.message, collection=collection)
    return ChatResponse(answer=answer, citations=[CitationOut(**c) for c in citations])


async def _resolve_collection(conversation, topic_repo: TopicRepoDep) -> str | None:  # noqa: ANN001
    if conversation.topic_id is None:
        return None
    topic = await topic_repo.get(conversation.topic_id)
    return topic.qdrant_collection if topic else None


@router.post("/{conversation_id}/messages/stream")
async def stream_message(
    conversation_id: uuid.UUID,
    body: ChatRequest,
    user: CurrentUserDep,
    repo: ConversationRepoDep,
    topic_repo: TopicRepoDep,
    streamer: StreamingChatServiceDep,
) -> StreamingResponse:
    """Stream the answer token-by-token (SSE). Set ``thinking`` to also stream reasoning."""
    conversation = await repo.get(conversation_id)
    if conversation is None or conversation.user_id != user.id:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if not conversation.title:  # auto-name from the first message
        conversation.title = _short_title(body.message)
    collection = await _resolve_collection(conversation, topic_repo)

    async def event_stream():
        async for event in streamer.stream(
            conversation_id, body.message, collection=collection, thinking=body.thinking
        ):
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/{conversation_id}/messages", response_model=list[MessageOut])
async def list_messages(
    conversation_id: uuid.UUID, user: CurrentUserDep, repo: ConversationRepoDep
) -> list[MessageOut]:
    conversation = await repo.get(conversation_id)
    if conversation is None or conversation.user_id != user.id:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return [MessageOut.model_validate(m) for m in await repo.list_messages(conversation_id)]
