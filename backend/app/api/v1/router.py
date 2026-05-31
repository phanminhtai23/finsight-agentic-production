"""Aggregates all v1 routers."""

from fastapi import APIRouter

from app.api.v1.routes import (
    auth,
    conversations,
    documents,
    health,
    qa,
    skills,
    tasks,
    topics,
    ws,
)

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(qa.router, tags=["qa"])
api_router.include_router(topics.router, prefix="/topics", tags=["topics"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
api_router.include_router(conversations.router, prefix="/conversations", tags=["conversations"])
api_router.include_router(skills.router, prefix="/skills", tags=["skills"])
api_router.include_router(ws.router, prefix="/ws", tags=["ws"])
