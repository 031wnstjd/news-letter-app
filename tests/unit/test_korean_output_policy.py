from newsletter_api.newsletter.pipeline import build_daily_newsletter
from newsletter_api.summarization.client import SummaryResult, summarize_text


def test_fallback_summary_lines_are_korean():
    result = summarize_text('Engineers shipped a new distributed runtime update.')
    assert result.ok is True
    assert any('핵심' in line or '중요' in line or '적용' in line for line in result.lines)


def test_fallback_summary_reflects_input_text():
    text = "새로운 런타임이 배포되었습니다. 콜드스타트 시간이 30% 감소했습니다. 운영 비용이 절감됩니다."
    result = summarize_text(text)
    assert result.ok is True
    joined = " ".join(result.lines)
    assert "콜드스타트" in joined or "30%" in joined


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
    monkeypatch.setattr('newsletter_api.newsletter.pipeline.fetch_article_text', lambda _url: "")

    result = build_daily_newsletter(limit=2)
    assert result['hot'][0]['title'] == '번역된 제목'
    assert result['subject'].startswith('[AI 개발 데일리]')
    assert "### 핵심 요약" in result['hot'][0]['markdown']
    assert "### 실무 적용" in result['hot'][0]['markdown']


def test_preview_uses_article_body_for_ai_input(monkeypatch):
    monkeypatch.setattr(
        'newsletter_api.newsletter.pipeline._collect_candidates',
        lambda: [
            {
                'title': 'OpenAI releases new API',
                'url': 'https://example.com/a',
                'summary': 'RSS 요약 텍스트',
                'published': '',
                'source_domain': 'example.com',
                'category': 'LLM/Agent',
                'trust_tier': 'T1',
                'canonical_url': 'https://example.com/a',
                'age_hours': 1,
                'score': 0.9,
            }
        ],
    )
    monkeypatch.setattr(
        'newsletter_api.newsletter.pipeline.fetch_article_text',
        lambda _url: "실제 본문 내용 첫 문장입니다. 실제 본문 내용 두 번째 문장입니다.",
    )

    captured = {}

    def fake_summarize_item(_self, title, source_text, url):
        captured['source_text'] = source_text
        return SummaryResult(
            lines=['요약 1', '요약 2', '왜 중요한가', '실무 적용', '세부 포인트 1'],
            ok=True,
            translated_title='번역된 제목',
        )

    monkeypatch.setattr('newsletter_api.newsletter.pipeline.AISummarizer.summarize_item', fake_summarize_item)

    result = build_daily_newsletter(limit=1)
    assert "실제 본문 내용" in captured['source_text']
    assert "RSS 요약 텍스트" in captured['source_text']
    assert len(result['hot'][0]['lines']) >= 4
    assert "### 참고" in result['hot'][0]['markdown']
