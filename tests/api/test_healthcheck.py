from fastapi.testclient import TestClient

from newsletter_api.main import app


def test_healthcheck_returns_ok():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
