"""Unit tests for password hashing and JWT helpers."""

import jwt
import pytest

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_password_hash_roundtrip():
    hashed = hash_password("s3cret-password")
    assert verify_password("s3cret-password", hashed)
    assert not verify_password("wrong", hashed)


def test_access_token_roundtrip():
    token = create_access_token("user-123")
    payload = decode_token(token, expected_type="access")
    assert payload["sub"] == "user-123"
    assert payload["type"] == "access"


def test_token_type_is_enforced():
    refresh = create_refresh_token("user-123")
    with pytest.raises(jwt.InvalidTokenError):
        decode_token(refresh, expected_type="access")
