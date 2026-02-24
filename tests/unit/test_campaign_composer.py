from newsletter_api.campaign.composer import compose_campaign


def sample_issue_set() -> dict:
    return {
        "subject": "[AI/Dev Daily] test",
        "badge": "오늘은 검증 통과 8개 발행",
        "hot": [
            {
                "title": "Hot1",
                "url": "https://example.com/1",
                "source_domain": "example.com",
                "tldr": "summary",
            },
            {
                "title": "Hot2",
                "url": "https://example.com/2",
                "source_domain": "example.com",
                "tldr": "summary",
            },
        ],
        "bottom": [
            {"title": "B1", "url": "https://example.com/b1", "source_domain": "example.com"},
            {"title": "B2", "url": "https://example.com/b2", "source_domain": "example.com"},
        ],
        "satisfaction_url": "https://example.com/sat",
        "unsubscribe_url": "https://example.com/unsub",
    }


def test_compose_campaign_returns_html_and_text():
    result = compose_campaign(sample_issue_set())
    assert "<html" in result.html.lower()
    assert "Hot Issue" in result.text
