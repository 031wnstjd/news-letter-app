from types import SimpleNamespace

from newsletter_api.ingestion.rss_fetcher import fetch_rss_items


class FakeFeed:
    def __init__(self):
        self.entries = [
            SimpleNamespace(
                title='Sample title',
                link='https://example.com/post?utm_source=x',
                summary='Summary text',
                published='Tue, 24 Feb 2026 01:00:00 GMT',
            )
        ]


def test_fetch_rss_items_normalizes_entry_fields(monkeypatch):
    def fake_fetch_xml(url: str, timeout: float = 4.0):
        assert url == 'https://example.com/feed.xml'
        assert timeout == 4.0
        return "<rss>dummy</rss>"

    def fake_parse(content: str):
        assert content == "<rss>dummy</rss>"
        return FakeFeed()

    monkeypatch.setattr('newsletter_api.ingestion.rss_fetcher._fetch_feed_xml', fake_fetch_xml)
    monkeypatch.setattr('newsletter_api.ingestion.rss_fetcher.feedparser.parse', fake_parse)

    source = {
        'name': 'Example Source',
        'domain': 'example.com',
        'rss_url': 'https://example.com/feed.xml',
        'tags': ['LLM/Agent'],
    }
    items = fetch_rss_items(source)

    assert len(items) == 1
    assert items[0]['title'] == 'Sample title'
    assert items[0]['url'] == 'https://example.com/post?utm_source=x'
    assert items[0]['summary'] == 'Summary text'
    assert items[0]['source_domain'] == 'example.com'


def test_fetch_rss_items_returns_empty_on_network_error(monkeypatch):
    def fake_fetch_xml(_url: str, timeout: float = 4.0):
        raise RuntimeError("network fail")

    monkeypatch.setattr('newsletter_api.ingestion.rss_fetcher._fetch_feed_xml', fake_fetch_xml)
    source = {'rss_url': 'https://example.com/feed.xml'}
    assert fetch_rss_items(source) == []
