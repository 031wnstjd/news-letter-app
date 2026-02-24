from fastapi.testclient import TestClient

from newsletter_api.delivery.redirect import encode_redirect_token
from newsletter_api.delivery.suppression import SuppressionPolicy
from newsletter_api.main import app


def test_redirect_endpoint_returns_302():
    client = TestClient(app)
    token = encode_redirect_token("https://example.com/article")
    response = client.get(f"/r/{token}", follow_redirects=False)
    assert response.status_code == 302


def test_soft_bounce_three_times_suppresses():
    policy = SuppressionPolicy()
    assert policy.apply_event("a@example.com", "soft_bounce") is False
    assert policy.apply_event("a@example.com", "soft_bounce") is False
    assert policy.apply_event("a@example.com", "soft_bounce") is True
