from newsletter_api.ingestion.pipeline import normalize_feed_item


def test_normalize_feed_item_strips_tracking_params():
    raw = {"url": "https://example.com/post?a=1&utm_source=x", "title": "t"}
    item = normalize_feed_item(raw)
    assert item.canonical_url == "https://example.com/post?a=1"
