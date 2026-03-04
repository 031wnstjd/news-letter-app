from newsletter_api.newsletter.pipeline import build_daily_newsletter
from newsletter_api.summarization.client import SummaryResult, summarize_text


def test_fallback_summary_lines_are_korean():
    result = summarize_text('Engineers shipped a new distributed runtime update.')
    assert result.ok is True
    assert any('핵심' in line or '중요' in line or '적용' in line for line in result.lines)


def test_preview_prefers_korean_translated_title(monkeypatch):
    monkeypatch.setattr(
        'newsletter_api.newsletter.pipeline._collect_candidates',
        lambda: [
            {
                'title': 'OpenAI releases new API',
                'url': 'https://example.com/a',
                'summary': 'English summary',
                'published': '',
                'source_domain': 'example.com',
                'category': 'LLM/Agent',
                'trust_tier': 'T1',
                'canonical_url': 'https://example.com/a',
                'age_hours': 1,
                'score': 0.9,
            },
            {
                'title': 'Second title',
                'url': 'https://example.com/b',
                'summary': 'English summary',
                'published': '',
                'source_domain': 'example.com',
                'category': 'Backend',
                'trust_tier': 'T1',
                'canonical_url': 'https://example.com/b',
                'age_hours': 1,
                'score': 0.8,
            },
        ],
    )

    def fake_summarize_item(_self, title, source_text, url):
        return SummaryResult(
            lines=['요약 1', '요약 2', '왜 중요한가', '실무 적용'],
            ok=True,
            translated_title='번역된 제목',
        )

    monkeypatch.setattr('newsletter_api.newsletter.pipeline.AISummarizer.summarize_item', fake_summarize_item)

    result = build_daily_newsletter(limit=2)
    assert result['hot'][0]['title'] == '번역된 제목'
    assert result['subject'].startswith('[AI 개발 데일리]')
