from fastapi.testclient import TestClient

from newsletter_api.main import app


def test_newsletter_preview_endpoint_returns_slots(monkeypatch):
    def fake_build_daily_newsletter(limit: int = 8):
        return {
            'subject': '[AI/Dev Daily] Preview',
            'badge': '오늘은 검증 통과 8개 발행',
            'hot': [{'title': 'h1'}, {'title': 'h2'}],
            'bottom': [{'title': 'b1'} for _ in range(6)],
            'ai_used': True,
        }

    monkeypatch.setattr('newsletter_api.newsletter.routes.build_daily_newsletter', fake_build_daily_newsletter)

    client = TestClient(app)
    response = client.get('/v1/newsletter/preview')

    assert response.status_code == 200
    body = response.json()
    assert body['subject'] == '[AI/Dev Daily] Preview'
    assert len(body['hot']) == 2
    assert len(body['bottom']) == 6
