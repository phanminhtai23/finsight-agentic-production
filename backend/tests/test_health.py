"""Smoke test for the health endpoint."""

from fastapi.testclient import TestClient


def test_health_ok(client: TestClient) -> None:
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["app"] == "FinSight"


def test_health_sets_request_id_header(client: TestClient) -> None:
    resp = client.get("/api/v1/health")
    assert resp.headers.get("X-Request-ID")


def test_readiness_reports_dependencies(client: TestClient) -> None:
    # Without live Postgres/Redis/Qdrant this returns 503 (degraded); with them, 200 (ready).
    resp = client.get("/api/v1/readiness")
    assert resp.status_code in (200, 503)
    body = resp.json()
    assert set(body["dependencies"]) == {"database", "redis", "qdrant"}


def test_metrics_endpoint_exposes_prometheus(client: TestClient) -> None:
    resp = client.get("/metrics")
    assert resp.status_code == 200
    assert "finsight_http_requests_total" in resp.text
