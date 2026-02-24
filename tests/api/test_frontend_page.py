from fastapi.testclient import TestClient

from newsletter_api.main import app


def test_frontend_root_page_renders():
    client = TestClient(app)
    response = client.get('/')
    assert response.status_code == 200
    assert 'AI Dev Daily' in response.text
    assert '오늘의 프리뷰 생성' in response.text
