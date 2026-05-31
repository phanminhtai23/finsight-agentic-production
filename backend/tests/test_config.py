"""Tests for production configuration validation (fail-fast on insecure settings)."""

import pytest
from pydantic import ValidationError

from app.core.config import DEFAULT_JWT_SECRET, Settings

STRONG_SECRET = "x" * 48


def test_dev_allows_default_secret():
    s = Settings(environment="dev", jwt_secret=DEFAULT_JWT_SECRET)
    assert s.environment == "dev"


def test_prod_rejects_default_secret():
    with pytest.raises(ValidationError):
        Settings(environment="prod", jwt_secret=DEFAULT_JWT_SECRET, google_api_key="k")


def test_prod_rejects_short_secret():
    with pytest.raises(ValidationError):
        Settings(environment="prod", jwt_secret="too-short", google_api_key="k")


def test_prod_requires_google_api_key():
    with pytest.raises(ValidationError):
        Settings(environment="prod", jwt_secret=STRONG_SECRET, google_api_key=None)


def test_prod_accepts_strong_config():
    s = Settings(environment="prod", jwt_secret=STRONG_SECRET, google_api_key="real-key")
    assert s.is_prod
