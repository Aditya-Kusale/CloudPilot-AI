"""API health endpoint tests."""
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_health_endpoint_returns_ok() -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "cloudpilot-api"}

def test_root_endpoint_returns_service_information() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "running"
