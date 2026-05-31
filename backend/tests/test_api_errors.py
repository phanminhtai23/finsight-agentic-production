"""API integration tests for auth and the structured error envelope.

These exercise the request → middleware → exception-handler path without external services:
auth rejection, request validation, and unknown routes all return the consistent
``{"error": {...}}`` envelope with a correlation id.
"""

from fastapi.testclient import TestClient


def test_protected_route_requires_auth(client: TestClient) -> None:
    # No Authorization header → 401 from the auth dependency, wrapped in the error envelope.
    resp = client.post(
        "/api/v1/conversations/00000000-0000-0000-0000-000000000000/messages/stream",
        json={"message": "hello"},
    )
    assert resp.status_code == 401
    body = resp.json()
    assert body["error"]["code"] == "http_error"
    assert "request_id" in body["error"]


def test_validation_error_envelope(client: TestClient) -> None:
    # Missing required "question" field → 422 with structured details.
    resp = client.post("/api/v1/ask", json={})
    assert resp.status_code == 422
    body = resp.json()
    assert body["error"]["code"] == "validation_error"
    assert isinstance(body["error"]["details"], list)


def test_unknown_route_returns_envelope(client: TestClient) -> None:
    resp = client.get("/api/v1/definitely-not-a-route")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "http_error"


def test_request_id_is_echoed_when_supplied(client: TestClient) -> None:
    resp = client.get("/api/v1/health", headers={"X-Request-ID": "test-correlation-123"})
    assert resp.headers.get("X-Request-ID") == "test-correlation-123"
