"""Tests for independent simulated CloudPilot sessions."""
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_provider_sessions_are_independent() -> None:
    client.post("/api/v1/sessions/end-all")
    aws = client.post("/api/v1/sessions/aws/start")
    azure = client.post("/api/v1/sessions/azure/start")
    assert aws.status_code == 200
    assert azure.status_code == 200

    ended = client.post("/api/v1/sessions/aws/end")
    assert ended.status_code == 200
    snapshot = client.get("/api/v1/sessions").json()
    by_provider = {item["provider"]: item for item in snapshot["providers"]}
    assert by_provider["aws"]["session"] is None
    assert by_provider["azure"]["session"]["status"] == "active"


def test_end_all_sessions() -> None:
    client.post("/api/v1/sessions/end-all")
    client.post("/api/v1/sessions/gcp/start")
    response = client.post("/api/v1/sessions/end-all")
    assert response.status_code == 200
    assert response.json()["ended_count"] >= 1
    snapshot = client.get("/api/v1/sessions").json()
    assert snapshot["active_sessions"] == 0


def test_invalid_provider_is_rejected() -> None:
    response = client.post("/api/v1/sessions/oracle/start")
    assert response.status_code == 404
