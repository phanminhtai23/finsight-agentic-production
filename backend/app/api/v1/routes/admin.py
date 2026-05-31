"""Admin endpoints — user analytics and management. All require an admin account."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import AdminServiceDep, AdminUserDep, SessionDep, require_admin
from app.schemas.admin import AdminStats, AdminUserOut
from app.services.admin_service import AdminError

# Every route in this router requires an authenticated admin.
router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("/stats", response_model=AdminStats)
async def stats(admin: AdminServiceDep) -> AdminStats:
    """Aggregate metrics for the admin dashboard (totals, distributions, time series)."""
    return await admin.stats()


@router.get("/users", response_model=list[AdminUserOut])
async def list_users(admin: AdminServiceDep) -> list[AdminUserOut]:
    """All users with per-user document / conversation / message (request) counts."""
    return await admin.list_users()


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: uuid.UUID,
    admin: AdminServiceDep,
    current: AdminUserDep,
    session: SessionDep,
) -> None:
    """Delete a user and all of their data (topics + Qdrant collections, documents, chats)."""
    try:
        await admin.delete_user(user_id, requester_id=current.id)
    except AdminError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    await session.commit()
