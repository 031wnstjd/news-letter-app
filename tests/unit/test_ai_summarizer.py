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
                                'tldr': ['line1', 'line2'],
                                'why_it_matters': 'important',
                                'practical_apply': 'do this',
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
    assert result.lines[0] == 'line1'
    assert result.lines[1] == 'line2'
    assert result.lines[2] == 'important'
    assert result.lines[3] == 'do this'


def test_ai_summarizer_returns_error_without_api_key():
    summarizer = AISummarizer(api_key='')
    result = summarizer.summarize_item('Title', 'Body', 'https://example.com')
    assert result.ok is False
    assert 'OPENAI_API_KEY' in result.error
