import httpx

from newsletter_api.ingestion.html_fetcher import fetch_article_text


def test_fetch_article_text_extracts_article_paragraphs():
    def handler(_request: httpx.Request) -> httpx.Response:
        html = """
        <html>
          <body>
            <article>
              <p>첫 번째 문단입니다.</p>
              <p>두 번째 문단입니다.</p>
            </article>
          </body>
        </html>
        """
        return httpx.Response(200, text=html, headers={"content-type": "text/html; charset=utf-8"})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    text = fetch_article_text("https://example.com/post", client=client)
    assert "첫 번째 문단입니다." in text
    assert "두 번째 문단입니다." in text


def test_fetch_article_text_returns_empty_on_http_error():
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="server error")

    client = httpx.Client(transport=httpx.MockTransport(handler))
    text = fetch_article_text("https://example.com/post", client=client)
    assert text == ""
