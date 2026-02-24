from fastapi.testclient import TestClient

from newsletter_api.main import app


def test_subscribe_and_verify_flow():
    client = TestClient(app)
    create = client.post("/v1/subscribers", json={"email": "dev@example.com"})
    assert create.status_code == 202
    token = create.json()["verification_token"]
    verify = client.post(f"/v1/subscribers/verify/{token}")
    assert verify.status_code == 200
    assert verify.json() == {"status": "verified"}
