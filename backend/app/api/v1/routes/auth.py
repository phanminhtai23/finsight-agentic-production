"""Authentication endpoints."""

import os
import tempfile
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.api.deps import AuthServiceDep, CurrentUserDep, SessionDep, SettingsDep, UserRepoDep
from app.rag.ingestion.storage import get_file_storage
from app.schemas.auth import (
    AccessTokenResponse,
    GoogleLoginRequest,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
    UpdateProfileRequest,
    UserOut,
)
from app.schemas.topic import UsageOut
from app.services.auth_service import AuthError

router = APIRouter()


def _unauthorized(exc: AuthError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))


@router.get("/me/usage", response_model=UsageOut)
async def usage(user: CurrentUserDep, settings: SettingsDep) -> UsageOut:
    quota = settings.storage_quota_mb * 1024 * 1024
    used = user.storage_used_bytes or 0
    return UsageOut(
        used_bytes=used,
        quota_bytes=quota,
        quota_mb=settings.storage_quota_mb,
        percent=round(used / quota * 100, 2) if quota else 0.0,
    )


@router.post("/register", response_model=RegisterResponse, status_code=201)
async def register(
    body: RegisterRequest, auth: AuthServiceDep, session: SessionDep
) -> RegisterResponse:
    try:
        user, dev_token = await auth.register(body.email, body.password, body.full_name)
    except AuthError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    await session.commit()
    return RegisterResponse(user=UserOut.model_validate(user), verification_token=dev_token)


@router.get("/verify-email", response_model=UserOut)
async def verify_email(token: str, auth: AuthServiceDep, session: SessionDep) -> UserOut:
    try:
        user = await auth.verify_email(token)
    except AuthError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    await session.commit()
    return UserOut.model_validate(user)


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, auth: AuthServiceDep) -> TokenResponse:
    try:
        user = await auth.authenticate(body.email, body.password)
    except AuthError as exc:
        raise _unauthorized(exc) from exc
    access, refresh = auth.issue_tokens(user)
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/google", response_model=TokenResponse)
async def login_google(
    body: GoogleLoginRequest, auth: AuthServiceDep, session: SessionDep
) -> TokenResponse:
    try:
        user = await auth.login_with_google(body.id_token)
    except AuthError as exc:
        raise _unauthorized(exc) from exc
    await session.commit()
    access, refresh = auth.issue_tokens(user)
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/refresh", response_model=AccessTokenResponse)
async def refresh(body: RefreshRequest, auth: AuthServiceDep) -> AccessTokenResponse:
    try:
        access = await auth.refresh_access(body.refresh_token)
    except AuthError as exc:
        raise _unauthorized(exc) from exc
    return AccessTokenResponse(access_token=access)


@router.get("/me", response_model=UserOut)
async def me(user: CurrentUserDep) -> UserOut:
    return UserOut.model_validate(user)


@router.patch("/me", response_model=UserOut)
async def update_me(
    body: UpdateProfileRequest, user: CurrentUserDep, session: SessionDep
) -> UserOut:
    if body.full_name is not None:
        user.full_name = body.full_name
    await session.commit()
    return UserOut.model_validate(user)


@router.post("/me/avatar", response_model=UserOut)
async def update_avatar(
    user: CurrentUserDep,
    settings: SettingsDep,
    session: SessionDep,
    user_repo: UserRepoDep,
    file: Annotated[UploadFile, File()],
) -> UserOut:
    suffix = Path(file.filename or "avatar.png").suffix or ".png"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name
    try:
        _, url = await get_file_storage(settings).upload(tmp_path)
    finally:
        os.unlink(tmp_path)
    user.avatar_url = url
    await session.commit()
    return UserOut.model_validate(user)
