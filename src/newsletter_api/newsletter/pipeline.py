from __future__ import annotations

from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse

from newsletter_api.dedup.service import should_merge_by_mixed_rule
from newsletter_api.ingestion.html_fetcher import fetch_article_text
from newsletter_api.ingestion.pipeline import canonicalize_url
from newsletter_api.ingestion.rss_fetcher import fetch_rss_items
from newsletter_api.ranking.allocator import allocate_slots
from newsletter_api.ranking.scorer import score
from newsletter_api.sources_loader import load_sources
from newsletter_api.summarization.client import AISummarizer, summarize_text

COMMUNITY_PREFERRED_DOMAINS = {
    "news.hada.io",
    "news.ycombinator.com",
    "lobste.rs",
    "reddit.com",
    "techmeme.com",
    "dev.to",
    "slashdot.org",
    "daily.dev",
    "yozm.wishket.com",
}
HEAVY_RESEARCH_DOMAINS = {
    "arxiv.org",
    "research.google",
    "ai.meta.com",
}


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
        domain = (item.get("source_domain") or "").lower()
        source_adjust = 0.0
        if any(preferred in domain for preferred in COMMUNITY_PREFERRED_DOMAINS):
            source_adjust += 0.12
        if any(heavy in domain for heavy in HEAVY_RESEARCH_DOMAINS):
            source_adjust -= 0.18
        raw_score = score(recency, authority, impact, penalty) + source_adjust
        item["score"] = max(0.0, min(raw_score, 1.0))
    return sorted(candidates, key=lambda x: x.get("score", 0.0), reverse=True)


def _build_source_text(item: dict) -> str:
    article_text = fetch_article_text(item.get("url", ""))
    feed_summary = (item.get("summary") or "").strip()
    title = (item.get("title") or "").strip()

    parts: list[str] = []
    if article_text:
        parts.append(f"[기사 본문]\n{article_text}")
    if feed_summary:
        parts.append(f"[피드 요약]\n{feed_summary}")
    if title:
        parts.append(f"[원문 제목]\n{title}")
    return "\n\n".join(parts).strip()


def _summarize_item(item: dict, summarizer: AISummarizer) -> tuple[list[str], bool, str, str]:
    text = _build_source_text(item) or item.get("summary") or item.get("title") or ""
    ai_result = summarizer.summarize_item(item.get("title", ""), text, item.get("url", ""))
    if ai_result.ok:
        return ai_result.lines, True, ai_result.translated_title, ""
    fallback = summarize_text(text)
    return fallback.lines, False, "", ai_result.error


def _strip_label(text: str) -> str:
    for prefix in ("핵심 요약 1:", "핵심 요약 2:", "왜 중요한가:", "실무 적용:", "핵심 내용:", "리스크:", "실행 체크:"):
        if text.startswith(prefix):
            return text[len(prefix) :].strip()
    return text.strip()


def _split_detail_sections(lines: list[str]) -> tuple[list[str], list[str], list[str]]:
    core_points: list[str] = []
    risks: list[str] = []
    check_items: list[str] = []
    for line in lines[4:]:
        if line.startswith("리스크:"):
            risks.append(_strip_label(line))
            continue
        if line.startswith("실행 체크:"):
            check_items.append(_strip_label(line))
            continue
        core_points.append(_strip_label(line))
    return core_points, risks, check_items


def _to_view(item: dict, lines: list[str], display_title: str) -> dict:
    tldr = " ".join(lines[:2]).strip() if lines else ""
    summary_points = [_strip_label(line) for line in lines[:2] if line]
    why_it_matters = _strip_label(lines[2]) if len(lines) > 2 else ""
    practical_apply = _strip_label(lines[3]) if len(lines) > 3 else ""
    core_points, risks, check_items = _split_detail_sections(lines)

    markdown_lines = ["### 한눈에 보기"]
    if summary_points:
        markdown_lines.extend(f"- {point}" for point in summary_points)
    else:
        markdown_lines.append("- 핵심 요약을 생성하지 못했습니다.")
    markdown_lines.extend(["", "### 기사 핵심 내용"])
    if core_points:
        markdown_lines.extend(f"- {point}" for point in core_points)
    else:
        markdown_lines.append("- 본문 핵심 포인트를 추출하지 못했습니다.")
    markdown_lines.extend(["", "### 왜 중요한가", why_it_matters or "현재 이슈의 영향 범위를 추가 검토해야 합니다.", ""])
    markdown_lines.append("### 실무 적용 체크리스트")
    apply_steps = [step for step in [practical_apply, *check_items] if step and step.strip()]
    markdown_lines.extend(f"{idx}. {step}" for idx, step in enumerate(apply_steps, start=1))
    if not apply_steps:
        markdown_lines.append("1. 원문 근거를 다시 확인한 뒤 적용 여부를 판단하세요.")
    markdown_lines.extend(["", "### 리스크·주의사항"])
    if risks:
        markdown_lines.extend(f"- {risk}" for risk in risks)
    else:
        markdown_lines.append("- 운영 환경 반영 전 영향 범위와 롤백 전략을 함께 점검하세요.")
    markdown_lines.extend(
        [
            "",
            "### 참고",
            f"- 출처: {item.get('source_domain', '') or '알 수 없음'}",
            f"- 링크: {item.get('url', '')}",
        ]
    )

    return {
        "title": display_title,
        "url": item.get("url", ""),
        "source_domain": item.get("source_domain", ""),
        "category": item.get("category", "기타"),
        "score": round(item.get("score", 0.0), 3),
        "tldr": tldr,
        "lines": lines,
        "markdown": "\n".join(markdown_lines).strip(),
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
    ai_errors: list[str] = []
    rendered = []
    for item in picked:
        lines, used_ai, translated_title, ai_error = _summarize_item(item, summarizer)
        ai_used = ai_used or used_ai
        if ai_error:
            ai_errors.append(ai_error)
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
        "ai_error": ai_errors[0] if ai_errors else "",
    }
