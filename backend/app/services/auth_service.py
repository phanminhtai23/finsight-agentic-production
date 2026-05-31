"""Authentication: registration, login, email verification, refresh, Google sign-in."""

import uuid

import httpx
import jwt

from app.core.config import Settings
from app.core.email import send_verification_email
from app.core.logging import get_logger
from app.core.security import (
    create_access_token,
    create_email_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.repositories.user_repository import UserRepository

_GOOGLE_TOKENINFO = "https://oauth2.googleapis.com/tokeninfo"
log = get_logger(__name__)


class AuthError(Exception):
    """Raised on any authentication failure (mapped to 401/400 at the API layer)."""


class AuthService:
    def __init__(self, users: UserRepository, settings: Settings) -> None:
        self._users = users
        self._settings = settings

    async def register(
        self, email: str, password: str, full_name: str | None
    ) -> tuple[User, str | None]:
        email = email.lower()
        if await self._users.get_by_email(email):
            raise AuthError("Email already registered")
        user = await self._users.add(
            User(
                email=email,
                hashed_password=hash_password(password),
                full_name=full_name,
                is_verified=False,
                auth_provider="password",
            )
        )
        token = create_email_token(str(user.id))
        if self._settings.emails_enabled:
            link = f"{self._settings.frontend_url}/verify-email?token={token}"
            try:
                await send_verification_email(self._settings, user.email, link)
                return user, None
            except Exception as exc:  # noqa: BLE001 - fall back so setup can be debugged
                log.warning("verification_email_failed", error=str(exc))
                return user, token  # surface the token so the user can still verify
        return user, token

    async def authenticate(self, email: str, password: str) -> User:
        user = await self._users.get_by_email(email.lower())
        if user is None or not user.hashed_password:
            raise AuthError("Invalid email or password")
        if not verify_password(password, user.hashed_password):
            raise AuthError("Invalid email or password")
        if not user.is_verified:
            raise AuthError("Email not verified")
        return user

    async def verify_email(self, token: str) -> User:
        try:
            payload = decode_token(token, expected_type="verify")
        except jwt.PyJWTError as exc:
            raise AuthError("Invalid or expired verification link") from exc
        user = await self._users.get(uuid.UUID(payload["sub"]))
        if user is None:
            raise AuthError("User not found")
        user.is_verified = True
        return user

    async def refresh_access(self, refresh_token: str) -> str:
        try:
            payload = decode_token(refresh_token, expected_type="refresh")
        except jwt.PyJWTError as exc:
            raise AuthError("Invalid refresh token") from exc
        user = await self._users.get(uuid.UUID(payload["sub"]))
        if user is None:
            raise AuthError("User not found")
        return create_access_token(str(user.id))

    async def login_with_google(self, id_token: str) -> User:
        if not self._settings.google_oauth_enabled:
            raise AuthError("Google login is not configured")
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(_GOOGLE_TOKENINFO, params={"id_token": id_token})
        if resp.status_code != 200:
            raise AuthError("Invalid Google token")
        info = resp.json()
        if info.get("aud") != self._settings.google_oauth_client_id:
            raise AuthError("Google token audience mismatch")
        email = (info.get("email") or "").lower()
        if not email:
            raise AuthError("Google token has no email")

        user = await self._users.get_by_email(email)
        if user is None:
            user = await self._users.add(
                User(
                    email=email,
                    full_name=info.get("name"),
                    avatar_url=info.get("picture"),
                    is_verified=True,
                    auth_provider="google",
                )
            )
        return user

    @staticmethod
    def issue_tokens(user: User) -> tuple[str, str]:
        return create_access_token(str(user.id)), create_refresh_token(str(user.id))
