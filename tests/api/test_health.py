from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)

def test_health_check() -> None:
    """Test health endpoint returns 200 and status healthy."""
    response = client.get("/health/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data
    assert "version" in data
