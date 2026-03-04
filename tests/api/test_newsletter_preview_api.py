from fastapi.testclient import TestClient

from newsletter_api.main import app


def test_newsletter_preview_endpoint_returns_slots(monkeypatch):
    def fake_build_daily_newsletter(limit: int = 8):
        return {
            'subject': '[AI 개발 데일리] 프리뷰',
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
    assert body['subject'] == '[AI 개발 데일리] 프리뷰'
    assert len(body['hot']) == 2
    assert len(body['bottom']) == 6


def test_newsletter_preview_stream_emits_progress_and_done(monkeypatch):
    def fake_build_daily_newsletter(limit: int = 8, progress_callback=None):
        if progress_callback:
            progress_callback({'stage': 'start', 'message': '시작', 'percent': 5, 'current': 0, 'total': limit})
            progress_callback({'stage': 'summarizing', 'message': '요약 중', 'percent': 60, 'current': 1, 'total': limit})
        return {
            'subject': '[AI 개발 데일리] 프리뷰',
            'badge': '오늘은 검증 통과 2개 발행',
            'hot': [{'title': 'h1'}, {'title': 'h2'}],
            'bottom': [],
            'ai_used': True,
            'ai_error': '',
        }

    monkeypatch.setattr('newsletter_api.newsletter.routes.build_daily_newsletter', fake_build_daily_newsletter)

    client = TestClient(app)
    response = client.get('/v1/newsletter/preview/stream?limit=2')

    assert response.status_code == 200
    assert response.headers['content-type'].startswith('text/event-stream')
    assert 'event: progress' in response.text
    assert 'event: done' in response.text
    assert '[AI 개발 데일리] 프리뷰' in response.text
