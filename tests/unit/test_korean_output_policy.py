from newsletter_api.newsletter.pipeline import build_daily_newsletter
from newsletter_api.summarization.client import SummaryResult, summarize_text


def test_fallback_summary_lines_are_korean():
    result = summarize_text('Engineers shipped a new distributed runtime update.')
    assert result.ok is True
    assert any('핵심' in line or '중요' in line or '적용' in line for line in result.lines)
    assert any(line.startswith('핵심 사실:') for line in result.lines)
    assert any(line.startswith('주의사항:') for line in result.lines)
    assert any(line.startswith('실무 적용:') for line in result.lines)


def test_fallback_summary_reflects_input_text():
    text = "새로운 런타임이 배포되었습니다. 콜드스타트 시간이 30% 감소했습니다. 운영 비용이 절감됩니다."
    result = summarize_text(text)
    assert result.ok is True
    joined = " ".join(result.lines)
    assert "콜드스타트" in joined or "30%" in joined


def test_fallback_summary_keeps_korean_style_on_english_body():
    english_text = (
        "[기사 본문]\nPosted on Mar 4. I built a new vector conversion tool for developers. "
        "It reduces manual tracing time and improves output consistency."
    )
    result = summarize_text(english_text)
    assert result.ok is True
    assert result.lines[0].startswith("리드:")
    assert "Posted on Mar" not in " ".join(result.lines)


def test_fallback_summary_is_grounded_to_english_source_content():
    english_text = (
        "[기사 본문]\n"
        "Agentation helps developers click UI elements and generate precise CSS selectors. "
        "The tool reached 170k npm downloads and supports MCP sync for live feedback loops. "
        "Readout replays Claude Code sessions with a timeline of prompts, tool calls, and file edits."
    )
    result = summarize_text(english_text)
    assert result.ok is True
    joined = " ".join(result.lines)
    assert "Agentation" in joined
    assert "170k" in joined
    assert "Readout" in joined


def test_preview_prefers_korean_translated_title(monkeypatch):
    monkeypatch.setattr(
        'newsletter_api.newsletter.pipeline._collect_candidates',
        lambda *args, **kwargs: [
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
            lines=[
                '리드: 요약 리드',
                '무엇이 나왔나: 변경 1',
                '핵심 사실: 사실 1',
                '중요한 이유: 이유 1',
                '실무 적용: 적용 1',
                '주의사항: 주의 1',
            ],
            ok=True,
            translated_title='번역된 제목',
        )

    monkeypatch.setattr('newsletter_api.newsletter.pipeline.AISummarizer.summarize_item', fake_summarize_item)
    monkeypatch.setattr('newsletter_api.newsletter.pipeline.fetch_article_text', lambda _url, **_kwargs: "")

    result = build_daily_newsletter(limit=2)
    assert result['hot'][0]['title'] == '번역된 제목'
    assert result['subject'].startswith('[AI 개발 데일리]')
    assert "### 한눈에 보기" in result['hot'][0]['markdown']
    assert "### 왜 중요한가 (해설)" in result['hot'][0]['markdown']
    assert "### 실무 적용 시나리오" in result['hot'][0]['markdown']
    assert "### 인사이트" in result['hot'][0]['markdown']


def test_preview_uses_article_body_for_ai_input(monkeypatch):
    monkeypatch.setattr(
        'newsletter_api.newsletter.pipeline._collect_candidates',
        lambda *args, **kwargs: [
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
        lambda _url, **_kwargs: "실제 본문 내용 첫 문장입니다. 실제 본문 내용 두 번째 문장입니다.",
    )

    captured = {}

    def fake_summarize_item(_self, title, source_text, url):
        captured['source_text'] = source_text
        return SummaryResult(
            lines=[
                '리드: 요약 리드',
                '무엇이 나왔나: 변경 1',
                '핵심 사실: 사실 1',
                '중요한 이유: 이유 1',
                '실무 적용: 적용 1',
                '주의사항: 주의 1',
                '출처 메모: 메모 1',
            ],
            ok=True,
            translated_title='번역된 제목',
        )

    monkeypatch.setattr('newsletter_api.newsletter.pipeline.AISummarizer.summarize_item', fake_summarize_item)

    result = build_daily_newsletter(limit=1)
    assert "실제 본문 내용" in captured['source_text']
    assert "RSS 요약 텍스트" in captured['source_text']
    assert len(result['hot'][0]['lines']) >= 7
    assert "### 출처 메모" in result['hot'][0]['markdown']
    assert "### 원문 링크" in result['hot'][0]['markdown']


def test_preview_exposes_ai_error_when_all_ai_calls_fail(monkeypatch):
    monkeypatch.setattr(
        'newsletter_api.newsletter.pipeline._collect_candidates',
        lambda *args, **kwargs: [
            {
                'title': '테스트 제목',
                'url': 'https://example.com/a',
                'summary': '테스트 요약',
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
    monkeypatch.setattr('newsletter_api.newsletter.pipeline.fetch_article_text', lambda _url, **_kwargs: "")

    def fake_fail(_self, title, source_text, url):
        return SummaryResult(lines=[], ok=False, error="OPENAI_API_KEY가 설정되지 않았습니다.")

    monkeypatch.setattr('newsletter_api.newsletter.pipeline.AISummarizer.summarize_item', fake_fail)

    result = build_daily_newsletter(limit=1)
    assert result['ai_used'] is False
    assert "OPENAI_API_KEY" in result['ai_error']


def test_preview_marks_item_failed_when_ai_timeout(monkeypatch):
    monkeypatch.setattr(
        'newsletter_api.newsletter.pipeline._collect_candidates',
        lambda *args, **kwargs: [
            {
                'title': '타임아웃 테스트 제목',
                'url': 'https://example.com/a',
                'summary': '타임아웃 발생 시 실패 상태를 표시해야 합니다.',
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
    monkeypatch.setattr('newsletter_api.newsletter.pipeline.fetch_article_text', lambda _url, **_kwargs: "")

    def fake_timeout(_self, title, source_text, url):
        return SummaryResult(lines=[], ok=False, error="OpenAI 응답 시간이 초과되었습니다.")

    monkeypatch.setattr('newsletter_api.newsletter.pipeline.AISummarizer.summarize_item', fake_timeout)

    result = build_daily_newsletter(limit=1)
    assert result['ai_used'] is False
    assert "시간이 초과" in result['ai_error']
    assert result['hot'] or result['bottom']
    first = (result['hot'] + result['bottom'])[0]
    assert first['lines'] == []
    assert "AI 요약 실패" in first['markdown']


def test_preview_reports_progress_events(monkeypatch):
    monkeypatch.setattr(
        'newsletter_api.newsletter.pipeline._collect_candidates',
        lambda *args, **kwargs: [
            {
                'title': '테스트 제목',
                'url': 'https://example.com/a',
                'summary': '테스트 요약',
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
    monkeypatch.setattr('newsletter_api.newsletter.pipeline.fetch_article_text', lambda _url, **_kwargs: "")

    def fake_ok(_self, title, source_text, url):
        return SummaryResult(
            lines=[
                '리드: 요약 리드',
                '무엇이 나왔나: 변경 1',
                '핵심 사실: 사실 1',
                '중요한 이유: 이유 1',
                '실무 적용: 적용 1',
                '주의사항: 주의 1',
            ],
            ok=True,
            translated_title='번역된 제목',
        )

    monkeypatch.setattr('newsletter_api.newsletter.pipeline.AISummarizer.summarize_item', fake_ok)

    events = []
    result = build_daily_newsletter(limit=1, progress_callback=lambda payload: events.append(payload))
    assert result['ai_used'] is True
    stages = [event.get('stage') for event in events]
    assert 'start' in stages
    assert 'collect_done' in stages
    assert 'summarizing' in stages
    assert 'item_done' in stages
    assert 'done' in stages
    item_events = [event for event in events if event.get('stage') == 'item_done']
    assert item_events
    assert item_events[0].get('item', {}).get('markdown')
    assert item_events[0].get('item', {}).get('title')
