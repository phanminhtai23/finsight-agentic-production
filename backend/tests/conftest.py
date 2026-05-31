"""Shared pytest fixtures."""

import os

# Provide harmless defaults so service/embedder construction succeeds offline (no real calls
# are made in tests). Must run before the app/settings are imported and cached.
os.environ.setdefault("GOOGLE_API_KEY", "test-key")
os.environ.setdefault("JWT_SECRET", "test-secret-please-change-0123456789abcdef")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import create_app  # noqa: E402


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())
