from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from typing import Callable
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
SOURCE_SCAN_PRIORITY = (
    "news.hada.io",
    "news.ycombinator.com",
    "lobste.rs",
    "dev.to",
    "reddit.com",
    "github.blog",
    "openai.com",
    "aws.amazon.com",
    "kubernetes.io",
    "developer.chrome.com",
)

ProgressCallback = Callable[[dict], None]


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
    sources = [*groups.official, *groups.community]
    sources = [source for source in sources if source.get("enabled", True) and source.get("rss_url")]

    def _source_order(source: dict) -> tuple[int, str]:
        domain = str(source.get("domain", "")).lower()
        for idx, preferred in enumerate(SOURCE_SCAN_PRIORITY):
            if preferred in domain:
                return idx, domain
        return len(SOURCE_SCAN_PRIORITY), domain

    sources = sorted(sources, key=_source_order)
    source_scan_limit = max(8, min(16, (limit // 2) + 4))
    selected_sources = sources[:source_scan_limit]
    per_source_limit = 4

    items_by_index: dict[int, list[dict]] = {}
    max_workers = max(1, min(8, len(selected_sources)))
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {
            executor.submit(fetch_rss_items, source, per_source_limit): index
            for index, source in enumerate(selected_sources)
        }
        for future in as_completed(future_map):
            index = future_map[future]
            try:
                items_by_index[index] = future.result() or []
            except Exception:  # noqa: BLE001
                items_by_index[index] = []

    candidates: list[dict] = []
    for index, source in enumerate(selected_sources):
        for item in items_by_index.get(index, []):
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
    article_text = fetch_article_text(item.get("url", ""), timeout=4.0, max_chars=6000)
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
    for prefix in (
        "리드:",
        "무엇이 나왔나:",
        "핵심 사실:",
        "중요한 이유:",
        "실무 적용:",
        "주의사항:",
        "출처 메모:",
        "핵심 요약 1:",
        "핵심 요약 2:",
        "왜 중요한가:",
        "핵심 내용:",
        "리스크:",
        "실행 체크:",
    ):
        if text.startswith(prefix):
            return text[len(prefix) :].strip()
    return text.strip()


def _collect_prefixed(lines: list[str], prefix: str) -> list[str]:
    return [_strip_label(line) for line in lines if line.startswith(prefix)]


def _extract_sections(lines: list[str]) -> dict[str, list[str] | str]:
    lead = _collect_prefixed(lines, "리드:")
    what_happened = _collect_prefixed(lines, "무엇이 나왔나:")
    key_facts = _collect_prefixed(lines, "핵심 사실:")
    why = _collect_prefixed(lines, "중요한 이유:")
    practical = _collect_prefixed(lines, "실무 적용:")
    caveats = _collect_prefixed(lines, "주의사항:")
    source_notes = _collect_prefixed(lines, "출처 메모:")

    if not what_happened and len(lines) >= 2:
        what_happened = [_strip_label(lines[0]), _strip_label(lines[1])]
    if not key_facts:
        key_facts = _collect_prefixed(lines, "핵심 내용:")
    if not why and len(lines) > 2:
        why = [_strip_label(lines[2])]
    if not practical and len(lines) > 3:
        practical = [_strip_label(lines[3])]
    if not caveats:
        caveats = _collect_prefixed(lines, "리스크:")
    if not practical:
        practical = _collect_prefixed(lines, "실행 체크:")

    return {
        "lead": lead[0] if lead else "",
        "what_happened": what_happened,
        "key_facts": key_facts,
        "why": why,
        "practical": practical,
        "caveats": caveats,
        "source_notes": source_notes,
    }


def _to_view(item: dict, lines: list[str], display_title: str) -> dict:
    tldr = " ".join(lines[:2]).strip() if lines else ""
    sections = _extract_sections(lines)
    lead = str(sections["lead"])
    what_happened = list(sections["what_happened"])
    key_facts = list(sections["key_facts"])
    why = list(sections["why"])
    practical = list(sections["practical"])
    caveats = list(sections["caveats"])
    source_notes = list(sections["source_notes"])

    markdown_lines = ["### 🧭 먼저 결론"]
    if lead:
        markdown_lines.append(f"> {lead}")
    else:
        markdown_lines.append("> 이번 이슈의 핵심 흐름을 먼저 확인하세요.")

    markdown_lines.extend(["", "### 1) 이번 이슈에서 실제로 나온 것"])
    if what_happened:
        markdown_lines.extend(f"- {point}" for point in what_happened)
    else:
        markdown_lines.append("- 본문에서 확인된 변경 사항을 요약하지 못했습니다.")

    markdown_lines.extend(["", "### 2) 기사에서 확인된 핵심 사실"])
    if key_facts:
        markdown_lines.extend(f"- {point}" for point in key_facts)
    else:
        markdown_lines.append("- 핵심 사실을 충분히 추출하지 못했습니다.")

    markdown_lines.extend(["", "### 3) 왜 중요한가"])
    if why:
        markdown_lines.extend(f"- {point}" for point in why)
    else:
        markdown_lines.append("- 팀 우선순위와 운영 안정성 관점에서 추가 검토가 필요합니다.")

    markdown_lines.extend(["", "### 4) 실무 적용 가이드"])
    if practical:
        markdown_lines.extend(f"{idx}. {step}" for idx, step in enumerate(practical, start=1))
    else:
        markdown_lines.append("1. 원문 근거를 재확인한 뒤 적용 범위와 롤백 전략을 먼저 정의하세요.")

    markdown_lines.extend(["", "### 5) 주의할 점"])
    if caveats:
        markdown_lines.extend(f"- {risk}" for risk in caveats)
    else:
        markdown_lines.append("- 운영 환경 반영 전 영향 범위와 장애 대응 시나리오를 점검하세요.")

    if source_notes:
        markdown_lines.extend(["", "### 6) 출처 메모"])
        markdown_lines.extend(f"- {note}" for note in source_notes)
    markdown_lines.extend(
        [
            "",
            "### 원문 링크",
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


def _emit_progress(callback: ProgressCallback | None, payload: dict) -> None:
    if not callback:
        return
    try:
        callback(payload)
    except Exception:  # noqa: BLE001
        return


def build_daily_newsletter(limit: int = 8, progress_callback: ProgressCallback | None = None) -> dict:
    _emit_progress(
        progress_callback,
        {
            "stage": "start",
            "message": "뉴스 소스를 수집하는 중입니다...",
            "percent": 5,
            "current": 0,
            "total": limit,
        },
    )
    candidate_limit = max(32, limit * 6)
    candidates = _rank(_dedup(_collect_candidates(limit=candidate_limit)))
    _emit_progress(
        progress_callback,
        {
            "stage": "collect_done",
            "message": f"후보 {len(candidates)}건을 정리했습니다.",
            "percent": 20,
            "current": 0,
            "total": limit,
        },
    )
    if not candidates:
        _emit_progress(
            progress_callback,
            {
                "stage": "done",
                "message": "발행할 항목이 없습니다.",
                "percent": 100,
                "current": 0,
                "total": 0,
            },
        )
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
    rendered: list[dict | None] = [None] * len(picked)
    total = len(picked)

    def _summarize_job(job_item: dict) -> tuple[list[str], bool, str, str]:
        local_summarizer = AISummarizer(
            api_key=summarizer.api_key,
            model=summarizer.model,
            base_url=summarizer.base_url,
            timeout=summarizer.timeout,
        )
        return _summarize_item(job_item, local_summarizer)

    for index, item in enumerate(picked, start=1):
        _emit_progress(
            progress_callback,
            {
                "stage": "summarizing",
                "message": f"{index}/{total} 기사 요약 작업 등록: {item.get('title', '')[:60]}",
                "percent": 20,
                "current": 0,
                "total": total,
            },
        )

    max_workers = max(1, min(4, total))
    completed = 0
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {executor.submit(_summarize_job, item): idx for idx, item in enumerate(picked)}
        for future in as_completed(future_map):
            idx = future_map[future]
            item = picked[idx]
            lines, used_ai, translated_title, ai_error = future.result()
            ai_used = ai_used or used_ai
            if ai_error:
                ai_errors.append(ai_error)
            display_title = translated_title or item.get("title", "")
            rendered[idx] = _to_view(item, lines, display_title)
            completed += 1
            _emit_progress(
                progress_callback,
                {
                    "stage": "item_done",
                    "message": f"{completed}/{total} 기사 완료",
                    "percent": 20 + int(completed / max(total, 1) * 70),
                    "current": completed,
                    "total": total,
                    "title": display_title,
                    "index": idx,
                    "item": rendered[idx],
                },
            )

    ordered_rendered = [item for item in rendered if item is not None]

    hot = ordered_rendered[:2]
    bottom = ordered_rendered[2:]
    result = {
        "subject": f"[AI 개발 데일리] {datetime.now().date()} - 오늘의 핵심 {len(ordered_rendered)}개",
        "badge": f"오늘은 검증 통과 {len(ordered_rendered)}개 발행",
        "hot": hot,
        "bottom": bottom,
        "ai_used": ai_used,
        "ai_error": "" if ai_used else (ai_errors[0] if ai_errors else ""),
    }
    _emit_progress(
        progress_callback,
        {
            "stage": "done",
            "message": "프리뷰 생성이 완료되었습니다.",
            "percent": 100,
            "current": len(ordered_rendered),
            "total": len(ordered_rendered),
            "ai_used": ai_used,
        },
    )
    return result
