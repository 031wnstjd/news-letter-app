from __future__ import annotations

import feedparser

def fetch_rss_items(_source: dict, limit: int = 20) -> list[dict]:
    rss_url = _source.get("rss_url")
    if not rss_url:
        return []

    parsed = feedparser.parse(rss_url)
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
