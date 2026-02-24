from fastapi.testclient import TestClient

from newsletter_api.main import app


def test_generate_summary_endpoint_returns_structured_lines(monkeypatch):
    def fake_summarize_item(title: str, source_text: str, url: str):
        return {'ok': True, 'lines': ['a', 'b', 'c', 'd'], 'error': ''}

    monkeypatch.setattr('newsletter_api.summarization.routes.summarize_for_api', fake_summarize_item)

    client = TestClient(app)
    response = client.post(
        '/v1/summaries/generate',
        json={'title': 'T', 'url': 'https://example.com', 'source_text': 'Body'},
    )

    assert response.status_code == 200
    body = response.json()
    assert body['ok'] is True
    assert body['lines'] == ['a', 'b', 'c', 'd']
