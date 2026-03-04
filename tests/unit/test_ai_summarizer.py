import json

import httpx

from newsletter_api.summarization.client import AISummarizer


def test_ai_summarizer_parses_model_json_response():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith('/chat/completions')
        assert request.headers.get('Authorization', '').startswith('Bearer ')
        payload = {
            'choices': [
                {
                    'message': {
                        'content': json.dumps(
                            {
                                'lead': '핵심 리드',
                                'what_happened': ['변경점 1', '변경점 2'],
                                'key_facts': ['사실 1', '사실 2'],
                                'why_it_matters': ['중요성 1'],
                                'practical_steps': ['적용 1'],
                                'caveats': ['주의 1'],
                                'source_notes': ['메모 1'],
                            }
                        )
                    }
                }
            ]
        }
        return httpx.Response(200, json=payload)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    summarizer = AISummarizer(api_key='test-key', model='gpt-4o-mini', client=client)

    result = summarizer.summarize_item(
        title='Test title',
        source_text='Some long article text.',
        url='https://example.com/post',
    )

    assert result.ok is True
    assert result.lines[0] == '리드: 핵심 리드'
    assert result.lines[1] == '무엇이 나왔나: 변경점 1'
    assert result.lines[2] == '무엇이 나왔나: 변경점 2'
    assert result.lines[3] == '핵심 사실: 사실 1'
    assert any(line.startswith('주의사항:') for line in result.lines)


def test_ai_summarizer_returns_error_without_api_key():
    summarizer = AISummarizer(api_key='')
    result = summarizer.summarize_item('Title', 'Body', 'https://example.com')
    assert result.ok is False
    assert 'OPENAI_API_KEY' in result.error


def test_ai_summarizer_rescues_plain_text_response():
    def handler(_request: httpx.Request) -> httpx.Response:
        payload = {
            'choices': [
                {
                    'message': {
                        'content': '업데이트 핵심은 배포 안정성 개선입니다. 단계적으로 적용하고 지표를 확인하세요.'
                    }
                }
            ]
        }
        return httpx.Response(200, json=payload)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    summarizer = AISummarizer(api_key='test-key', model='gpt-4o-mini', client=client)
    result = summarizer.summarize_item('Test title', 'Body', 'https://example.com')
    assert result.ok is True
    assert any(line.startswith('리드:') for line in result.lines)


def test_ai_summarizer_default_timeout_is_three_minutes():
    summarizer = AISummarizer(api_key='test-key')
    assert summarizer.timeout == 180.0
