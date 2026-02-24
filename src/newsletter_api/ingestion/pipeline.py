from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from .html_fetcher import fetch_html_items
from .rss_fetcher import fetch_rss_items


@dataclass
class NormalizedItem:
    title: str
    url: str
    canonical_url: str


def canonicalize_url(url: str) -> str:
    parsed = urlparse(url)
    cleaned_q = [(k, v) for k, v in parse_qsl(parsed.query) if not k.lower().startswith("utm_")]
    return urlunparse(parsed._replace(query=urlencode(cleaned_q)))


def normalize_feed_item(raw: dict) -> NormalizedItem:
    url = raw.get("url", "")
    return NormalizedItem(
        title=raw.get("title", ""),
        url=url,
        canonical_url=canonicalize_url(url),
    )


def collect_items_for_source(source: dict) -> list[dict]:
    items = fetch_rss_items(source)
    if items:
        return items
    return fetch_html_items(source)
