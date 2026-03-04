from newsletter_api.campaign.composer import compose_campaign


def sample_issue_set() -> dict:
    return {
        "subject": "[AI 개발 데일리] 테스트",
        "badge": "오늘은 검증 통과 8개 발행",
        "hot": [
            {
                "title": "Hot1",
                "url": "https://example.com/1",
                "source_domain": "example.com",
                "tldr": "summary",
                "lines": ["핵심 1", "핵심 2", "왜 중요한가", "실무 적용", "세부 포인트"],
            },
            {
                "title": "Hot2",
                "url": "https://example.com/2",
                "source_domain": "example.com",
                "tldr": "summary",
                "lines": ["핵심 1", "핵심 2", "왜 중요한가", "실무 적용"],
            },
        ],
        "bottom": [
            {
                "title": "B1",
                "url": "https://example.com/b1",
                "source_domain": "example.com",
                "lines": ["핵심 1", "핵심 2", "왜 중요한가", "실무 적용"],
            },
            {
                "title": "B2",
                "url": "https://example.com/b2",
                "source_domain": "example.com",
                "lines": ["핵심 1", "핵심 2", "왜 중요한가", "실무 적용"],
            },
        ],
        "satisfaction_url": "https://example.com/sat",
        "unsubscribe_url": "https://example.com/unsub",
    }


def test_compose_campaign_returns_html_and_text():
    result = compose_campaign(sample_issue_set())
    assert "<html" in result.html.lower()
    assert "핵심 이슈" in result.text
    assert "왜 중요한가" in result.html
    assert "실무 적용" in result.text
