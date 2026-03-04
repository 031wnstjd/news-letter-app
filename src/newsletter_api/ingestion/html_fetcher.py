from __future__ import annotations

import html
import re

import httpx


_SCRIPT_STYLE_RE = re.compile(r"<(script|style|noscript)\b[^>]*>.*?</\1>", re.IGNORECASE | re.DOTALL)
_ARTICLE_RE = re.compile(r"<article\b[^>]*>(.*?)</article>", re.IGNORECASE | re.DOTALL)
_MAIN_RE = re.compile(r"<main\b[^>]*>(.*?)</main>", re.IGNORECASE | re.DOTALL)
_PARAGRAPH_RE = re.compile(r"<p\b[^>]*>(.*?)</p>", re.IGNORECASE | re.DOTALL)
_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def _normalize_text(fragment: str) -> str:
    text = _TAG_RE.sub(" ", fragment)
    text = html.unescape(text)
    text = _WS_RE.sub(" ", text).strip()
    return text


def _extract_scope(html_text: str) -> str:
    for pattern in (_ARTICLE_RE, _MAIN_RE):
        match = pattern.search(html_text)
        if match:
            return match.group(1)
    return html_text


def _extract_paragraphs(scope_text: str) -> list[str]:
    paragraphs = [_normalize_text(match.group(1)) for match in _PARAGRAPH_RE.finditer(scope_text)]
    paragraphs = [p for p in paragraphs if len(p) >= 8]
    return paragraphs


def fetch_article_text(
    url: str,
    *,
    timeout: float = 8.0,
    max_chars: int = 8000,
    client: httpx.Client | None = None,
) -> str:
    if not url.startswith(("http://", "https://")):
        return ""

    own_client = client is None
    http = client or httpx.Client(
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
    try:
        response = http.get(url)
        if response.status_code != 200:
            return ""
        content_type = (response.headers.get("content-type") or "").lower()
        if content_type and "html" not in content_type:
            return ""

        raw_html = response.text
        if not raw_html:
            return ""

        cleaned_html = _SCRIPT_STYLE_RE.sub(" ", raw_html)
        scope = _extract_scope(cleaned_html)
        paragraphs = _extract_paragraphs(scope)
        if len(" ".join(paragraphs)) < 200:
            paragraphs = _extract_paragraphs(cleaned_html)

        if not paragraphs:
            fallback = _normalize_text(scope)
            return fallback[:max_chars] if len(fallback) >= 80 else ""

        text = "\n".join(paragraphs)
        return text[:max_chars]
    except Exception:  # noqa: BLE001
        return ""
    finally:
        if own_client:
            http.close()


def fetch_html_items(_source: dict) -> list[dict]:
    # Placeholder for real HTML parsing in MVP skeleton.
    return []
