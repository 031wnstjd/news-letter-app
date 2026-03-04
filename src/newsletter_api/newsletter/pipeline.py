from __future__ import annotations

from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse

from newsletter_api.dedup.service import should_merge_by_mixed_rule
from newsletter_api.ingestion.pipeline import canonicalize_url
from newsletter_api.ingestion.rss_fetcher import fetch_rss_items
from newsletter_api.ranking.allocator import allocate_slots
from newsletter_api.ranking.scorer import score
from newsletter_api.sources_loader import load_sources
from newsletter_api.summarization.client import AISummarizer, summarize_text


def _parse_age_hours(published: str | None) -> int:
    if not published:
        return 999
    try:
        dt = parsedate_to_datetime(published)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return max(0, int((datetime.now(UTC) - dt).total_seconds() // 3600))
    except Exception:  # noqa: BLE001
        return 999


def _authority_by_tier(tier: str) -> float:
    return {"T1": 1.0, "T2": 0.75, "T3": 0.45}.get(tier, 0.6)


def _impact_score(item: dict) -> float:
    base = 0.5
    summary_len = len((item.get("summary") or "").strip())
    if summary_len > 300:
        base += 0.15
    if "reddit.com" in item.get("source_domain", "") or "news.ycombinator.com" in item.get("source_domain", ""):
        base += 0.1
    return min(base, 1.0)


def _commercial_penalty(item: dict) -> float:
    text = f"{item.get('title','')} {item.get('summary','')}".lower()
    keywords = ("sponsored", "limited time", "buy now", "promo")
    return 1.0 if any(k in text for k in keywords) else 0.0


def _collect_candidates(limit: int = 120) -> list[dict]:
    groups = load_sources("sources.yaml")
    candidates: list[dict] = []
    for source in [*groups.official, *groups.community]:
        items = fetch_rss_items(source, limit=10)
        for item in items:
            item["canonical_url"] = canonicalize_url(item.get("url", ""))
            item["trust_tier"] = source.get("trust_tier", "T2")
            item["category"] = item.get("category") or (source.get("tags") or ["기타"])[0]
            item["age_hours"] = _parse_age_hours(item.get("published"))
            item["source_domain"] = item.get("source_domain") or source.get("domain", "")
            candidates.append(item)
            if len(candidates) >= limit:
                return candidates
    return candidates


def _dedup(candidates: list[dict]) -> list[dict]:
    deduped: list[dict] = []
    for item in candidates:
        duplicate = False
        for chosen in deduped:
            entity_a = urlparse(item.get("url", "")).netloc
            entity_b = urlparse(chosen.get("url", "")).netloc
            if should_merge_by_mixed_rule(
                item.get("canonical_url", ""),
                chosen.get("canonical_url", ""),
                item.get("title", ""),
                chosen.get("title", ""),
                entity_a == entity_b,
            ):
                duplicate = True
                break
        if not duplicate:
            deduped.append(item)
    return deduped


def _rank(candidates: list[dict]) -> list[dict]:
    for item in candidates:
        recency = max(0.0, 1.0 - (item.get("age_hours", 999) / 96.0))
        authority = _authority_by_tier(item.get("trust_tier", "T2"))
        impact = _impact_score(item)
        penalty = _commercial_penalty(item)
        item["score"] = score(recency, authority, impact, penalty)
    return sorted(candidates, key=lambda x: x.get("score", 0.0), reverse=True)


def _summarize_item(item: dict, summarizer: AISummarizer) -> tuple[list[str], bool, str]:
    text = item.get("summary") or item.get("title") or ""
    ai_result = summarizer.summarize_item(item.get("title", ""), text, item.get("url", ""))
    if ai_result.ok:
        return ai_result.lines, True, ai_result.translated_title
    fallback = summarize_text(text)
    return fallback.lines, False, ""


def _to_view(item: dict, lines: list[str], display_title: str) -> dict:
    tldr = " ".join(lines[:2]).strip() if lines else ""
    return {
        "title": display_title,
        "url": item.get("url", ""),
        "source_domain": item.get("source_domain", ""),
        "category": item.get("category", "기타"),
        "score": round(item.get("score", 0.0), 3),
        "tldr": tldr,
        "lines": lines,
    }


def build_daily_newsletter(limit: int = 8) -> dict:
    candidates = _rank(_dedup(_collect_candidates()))
    if not candidates:
        return {
            "subject": f"[AI 개발 데일리] {datetime.now().date()} - 발행할 항목 없음",
            "badge": "오늘은 수집된 아이템이 없습니다",
            "hot": [],
            "bottom": [],
            "ai_used": False,
        }

    allocation = allocate_slots(candidates)
    picked = allocation.hot + allocation.bottom
    picked = picked[:limit]

    summarizer = AISummarizer()
    ai_used = False
    rendered = []
    for item in picked:
        lines, used_ai, translated_title = _summarize_item(item, summarizer)
        ai_used = ai_used or used_ai
        display_title = translated_title or item.get("title", "")
        rendered.append(_to_view(item, lines, display_title))

    hot = rendered[:2]
    bottom = rendered[2:]
    return {
        "subject": f"[AI 개발 데일리] {datetime.now().date()} - 오늘의 핵심 {len(rendered)}개",
        "badge": f"오늘은 검증 통과 {len(rendered)}개 발행",
        "hot": hot,
        "bottom": bottom,
        "ai_used": ai_used,
    }
