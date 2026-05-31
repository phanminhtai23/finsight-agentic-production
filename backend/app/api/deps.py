"""FastAPI dependency wiring (composition root).

Keeps routers thin: they declare the service they need and the container builds it from a
request-scoped session plus the configured providers (Postgres for relational data, Qdrant
for vectors).
"""

import uuid
from collections.abc import AsyncIterator
from typing import Annotated

import jwt
import redis.asyncio as redis
from arq.connections import ArqRedis
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.graph import build_graph
from app.agents.mcp_web import McpWebSearch
from app.core.cache import create_redis_pool
from app.core.checkpointer import get_checkpointer
from app.core.config import Settings, get_settings
from app.core.db import get_session, get_sessionmaker
from app.core.llm import get_chat_model, get_embedder, get_text_generator
from app.core.qdrant import get_qdrant_client
from app.core.queue import get_arq_pool
from app.core.security import decode_token
from app.models.user import User
from app.rag.indexing.qdrant_store import QdrantVectorStore
from app.rag.retrieval.hybrid import HybridRetriever
from app.rag.retrieval.qdrant_backend import QdrantSearchBackend
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.task_repository import TaskRepository
from app.repositories.topic_repository import TopicRepository
from app.repositories.user_repository import UserRepository
from app.services.agent_service import AgentService
from app.services.auth_service import AuthService
from app.services.events import EventPublisher
from app.services.ingestion_service import IngestionService
from app.services.qa_service import QAService
from app.services.streaming_chat_service import StreamingChatService
from app.services.topic_service import TopicService
from app.skills.base import SkillRegistry
from app.skills.library import default_registry

SettingsDep = Annotated[Settings, Depends(get_settings)]
SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def get_redis_client(settings: SettingsDep) -> AsyncIterator[redis.Redis]:
    client = create_redis_pool(settings)
    try:
        yield client
    finally:
        await client.aclose()


RedisDep = Annotated[redis.Redis, Depends(get_redis_client)]
ArqDep = Annotated[ArqRedis, Depends(get_arq_pool)]


def get_document_repo(session: SessionDep) -> DocumentRepository:
    return DocumentRepository(session)


def get_conversation_repo(session: SessionDep) -> ConversationRepository:
    return ConversationRepository(session)


def get_task_repo(session: SessionDep) -> TaskRepository:
    return TaskRepository(session)


DocumentRepoDep = Annotated[DocumentRepository, Depends(get_document_repo)]
ConversationRepoDep = Annotated[ConversationRepository, Depends(get_conversation_repo)]
TaskRepoDep = Annotated[TaskRepository, Depends(get_task_repo)]


def get_event_publisher(redis_client: RedisDep) -> EventPublisher:
    return EventPublisher(redis_client)


EventPublisherDep = Annotated[EventPublisher, Depends(get_event_publisher)]


def get_vector_store() -> QdrantVectorStore:
    settings = get_settings()
    return QdrantVectorStore(
        get_qdrant_client(settings),
        collection=settings.qdrant_collection,
        dim=settings.embedding_dim,
    )


def get_qa_service() -> QAService:
    settings = get_settings()
    backend = QdrantSearchBackend(
        get_qdrant_client(settings), collection=settings.qdrant_collection
    )
    retriever = HybridRetriever(backend, get_embedder())
    return QAService(retriever, get_text_generator())


def get_ingestion_service(document_repo: DocumentRepoDep) -> IngestionService:
    return IngestionService(
        document_repo=document_repo,
        vector_store=get_vector_store(),
        embedder=get_embedder(),
        text_generator=get_text_generator(),
    )


QAServiceDep = Annotated[QAService, Depends(get_qa_service)]
IngestionServiceDep = Annotated[IngestionService, Depends(get_ingestion_service)]


# The compiled multi-agent graph is stateless (the checkpointer holds per-thread state),
# so it is built once and shared across requests.
_compiled_graph: object | None = None


def _make_retriever(collection: str | None) -> HybridRetriever | None:
    """Build a topic-scoped retriever for a Qdrant collection (None = skip document RAG)."""
    if not collection:
        return None
    settings = get_settings()
    backend = QdrantSearchBackend(get_qdrant_client(settings), collection=collection)
    return HybridRetriever(backend, get_embedder())


async def get_compiled_graph() -> object:
    global _compiled_graph
    if _compiled_graph is None:
        settings = get_settings()
        checkpointer = await get_checkpointer(settings)
        web_search = McpWebSearch(settings.mcp_server_url)
        _compiled_graph = build_graph(
            _make_retriever, get_text_generator(), web_search, checkpointer=checkpointer
        )
    return _compiled_graph


async def get_agent_service(conversation_repo: ConversationRepoDep) -> AgentService:
    return AgentService(await get_compiled_graph(), conversation_repo)


AgentServiceDep = Annotated[AgentService, Depends(get_agent_service)]


def get_streaming_chat_service() -> StreamingChatService:
    settings = get_settings()
    return StreamingChatService(
        _make_retriever,
        get_chat_model(),
        McpWebSearch(settings.mcp_server_url),
        get_sessionmaker(),
        get_text_generator(),
    )


StreamingChatServiceDep = Annotated[StreamingChatService, Depends(get_streaming_chat_service)]

_skill_registry: SkillRegistry | None = None


def get_skill_registry() -> SkillRegistry:
    global _skill_registry
    if _skill_registry is None:
        _skill_registry = default_registry()
    return _skill_registry


SkillRegistryDep = Annotated[SkillRegistry, Depends(get_skill_registry)]


# --- Auth ---
_bearer = HTTPBearer(auto_error=False)


def get_user_repo(session: SessionDep) -> UserRepository:
    return UserRepository(session)


UserRepoDep = Annotated[UserRepository, Depends(get_user_repo)]


def get_auth_service(user_repo: UserRepoDep, settings: SettingsDep) -> AuthService:
    return AuthService(user_repo, settings)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


async def get_current_user(
    user_repo: UserRepoDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> User:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        payload = decode_token(credentials.credentials, expected_type="access")
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        ) from exc
    user = await user_repo.get(uuid.UUID(payload["sub"]))
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


CurrentUserDep = Annotated[User, Depends(get_current_user)]


# --- Topics ---
def get_topic_repo(session: SessionDep) -> TopicRepository:
    return TopicRepository(session)


TopicRepoDep = Annotated[TopicRepository, Depends(get_topic_repo)]


def get_topic_service(
    topic_repo: TopicRepoDep, document_repo: DocumentRepoDep, settings: SettingsDep
) -> TopicService:
    return TopicService(topic_repo, document_repo, get_qdrant_client(settings), settings)


TopicServiceDep = Annotated[TopicService, Depends(get_topic_service)]
