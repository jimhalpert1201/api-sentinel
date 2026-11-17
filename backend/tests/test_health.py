import pytest
from app.main import app
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """FastAPI TestClient fixture."""
    return TestClient(app)


def test_health_check(client):
    """Verify system health endpoint returns 200 and expected status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "app" in data
    assert "version" in data
