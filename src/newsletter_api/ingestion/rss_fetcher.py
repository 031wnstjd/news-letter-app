from __future__ import annotations

import feedparser
import httpx


def _fetch_feed_xml(rss_url: str, timeout: float = 2.5) -> str:
    response = httpx.get(
        rss_url,
        timeout=timeout,
        follow_redirects=True,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            )
        },
    )
    response.raise_for_status()
    return response.text

def fetch_rss_items(_source: dict, limit: int = 20) -> list[dict]:
    rss_url = _source.get("rss_url")
    if not rss_url:
        return []

    try:
        xml_text = _fetch_feed_xml(rss_url)
        parsed = feedparser.parse(xml_text)
    except Exception:  # noqa: BLE001
        return []

    items: list[dict] = []
    for entry in parsed.entries[:limit]:
        items.append(
            {
                "title": getattr(entry, "title", ""),
                "url": getattr(entry, "link", ""),
                "summary": getattr(entry, "summary", ""),
                "published": getattr(entry, "published", ""),
                "source_name": _source.get("name", ""),
                "source_domain": _source.get("domain", ""),
                "category": (_source.get("tags") or ["기타"])[0],
            }
        )
    return items
