from __future__ import annotations

from dataclasses import dataclass
import json
import re

import httpx

from newsletter_api.config import Settings


@dataclass
class SummaryResult:
    lines: list[str]
    ok: bool
    error: str = ""
    translated_title: str = ""


class AISummarizer:
    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        client: httpx.Client | None = None,
        timeout: float = 20.0,
    ) -> None:
        settings = Settings()
        self.api_key = api_key if api_key is not None else settings.openai_api_key
        self.model = model if model is not None else settings.openai_model
        self.base_url = base_url if base_url is not None else settings.openai_base_url
        self.timeout = timeout
        self.client = client

    def summarize_item(self, title: str, source_text: str, url: str) -> SummaryResult:
        if not self.api_key:
            return SummaryResult(lines=[], ok=False, error="OPENAI_API_KEY가 설정되지 않았습니다.")
        if not source_text.strip():
            return SummaryResult(lines=[], ok=False, error="요약할 본문이 비어 있습니다.")

        prompt = (
            "반드시 JSON 객체로만 응답하세요. 키는 정확히 다음 5개만 사용하세요: "
            "translated_title(string), tldr(array[string] 길이 2), why_it_matters(string), "
            "practical_apply(string), key_points(array[string] 길이 2~3). "
            "모든 값은 한국어로 작성하고 영어 문장을 그대로 복사하지 말고 한국어로 의역하세요. "
            "문체는 논문 초록처럼 무겁지 않게, GeekNews 요약처럼 간결하고 실무 중심으로 작성하세요.\\n"
            f"원문 제목: {title}\\n원문 URL: {url}\\n원문 내용:\\n{source_text[:5000]}"
        )
        payload = {
            "model": self.model,
            "temperature": 0.2,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "당신은 기술 뉴스레터 에디터입니다. "
                        "반드시 한국어로만 작성하고 과장 없이 사실 중심으로 요약하세요. "
                        "학술 논문체 대신 개발자 커뮤니티 브리핑 스타일로 작성하세요."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
        }
        headers = {"Authorization": f"Bearer {self.api_key}"}

        own_client = self.client is None
        client = self.client or httpx.Client(timeout=self.timeout)
        try:
            response = client.post(f"{self.base_url}/chat/completions", json=payload, headers=headers)
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            content = content.strip()
            if content.startswith("```"):
                content = content.strip("`")
                if content.startswith("json"):
                    content = content[4:].strip()
            parsed = json.loads(content)
            tldr = parsed.get("tldr", [])
            if not isinstance(tldr, list):
                tldr = [str(tldr)]
            key_points = parsed.get("key_points", [])
            if isinstance(key_points, str):
                key_points = [key_points]
            if not isinstance(key_points, list):
                key_points = []
            lines = [
                str(tldr[0]) if len(tldr) > 0 else "",
                str(tldr[1]) if len(tldr) > 1 else "",
                str(parsed.get("why_it_matters", "")),
                str(parsed.get("practical_apply", "")),
            ]
            lines.extend(str(point) for point in key_points[:3])
            lines = [line.strip() for line in lines if line and line.strip()]
            if not lines:
                return SummaryResult(lines=[], ok=False, error="모델이 비어 있는 요약을 반환했습니다.")
            translated_title = str(parsed.get("translated_title", "")).strip()
            return SummaryResult(lines=lines, ok=True, translated_title=translated_title)
        except Exception:  # noqa: BLE001
            return SummaryResult(lines=[], ok=False, error="OpenAI 요청에 실패했습니다.")
        finally:
            if own_client:
                client.close()


_WS_RE = re.compile(r"\s+")
_SENTENCE_RE = re.compile(r"(?<=[.!?。！？])\s+")
_SECTION_HEADER_RE = re.compile(r"\[[^\]]+\]")
_HANGUL_RE = re.compile(r"[가-힣]")
_LATIN_RE = re.compile(r"[A-Za-z]")
_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9+._/-]{2,}|[가-힣]{2,}")
_EN_STOPWORDS = {
    "the",
    "and",
    "that",
    "with",
    "from",
    "this",
    "have",
    "will",
    "into",
    "about",
    "after",
    "before",
    "under",
    "using",
    "new",
    "posted",
    "post",
    "read",
    "comments",
    "comment",
    "jan",
    "feb",
    "mar",
    "apr",
    "may",
    "jun",
    "jul",
    "aug",
    "sep",
    "oct",
    "nov",
    "dec",
}


def _truncate(value: str, limit: int = 170) -> str:
    if len(value) <= limit:
        return value
    return f"{value[: limit - 1].rstrip()}…"


def _pick_sentences(text: str) -> list[str]:
    normalized = _WS_RE.sub(" ", text).strip()
    normalized = _SECTION_HEADER_RE.sub(" ", normalized)
    parts = [p.strip() for p in _SENTENCE_RE.split(normalized) if p.strip()]
    parts = [p for p in parts if len(p) >= 18]
    if parts:
        return parts

    if not normalized:
        return []

    chunked = []
    cursor = 0
    while cursor < len(normalized) and len(chunked) < 3:
        chunked.append(normalized[cursor : cursor + 150].strip())
        cursor += 150
    return [c for c in chunked if c]


def _extract_keywords(text: str, limit: int = 4) -> list[str]:
    tokens = _TOKEN_RE.findall(text)
    selected: list[str] = []
    for token in tokens:
        cleaned = token.strip(".,:;()[]{}\"'")
        if not cleaned:
            continue
        if cleaned.lower() in _EN_STOPWORDS:
            continue
        if len(cleaned) < 2:
            continue
        if cleaned in selected:
            continue
        selected.append(cleaned)
        if len(selected) >= limit:
            break
    return selected


def _is_korean_dominant(text: str) -> bool:
    hangul_count = len(_HANGUL_RE.findall(text))
    latin_count = len(_LATIN_RE.findall(text))
    return hangul_count >= 24 or hangul_count > latin_count


def _infer_topic(keywords: list[str]) -> str:
    lowered = {k.lower() for k in keywords}
    if lowered & {"agent", "llm", "gpt", "openai", "claude", "model", "inference"}:
        return "AI 모델·에이전트"
    if lowered & {"kubernetes", "docker", "devops", "cloud", "aws", "azure", "infra"}:
        return "인프라·DevOps"
    if lowered & {"react", "vue", "typescript", "javascript", "chrome", "frontend", "web"}:
        return "웹 프론트엔드"
    if lowered & {"postgres", "database", "sql", "redis", "backend"}:
        return "백엔드·데이터"
    return "개발 도구·플랫폼"


def summarize_text(text: str) -> SummaryResult:
    if not text.strip():
        return SummaryResult(lines=[], ok=False, error="요약할 본문이 비어 있습니다.")
    content_text = _SECTION_HEADER_RE.sub(" ", text)
    content_text = _WS_RE.sub(" ", content_text).strip()

    if _is_korean_dominant(content_text):
        sentences = _pick_sentences(content_text)
        first = _truncate(sentences[0]) if len(sentences) > 0 else "원문에서 핵심 내용을 추출했습니다."
        second = _truncate(sentences[1]) if len(sentences) > 1 else _truncate(first)
        third = _truncate(sentences[2]) if len(sentences) > 2 else "세부 맥락은 원문 링크에서 함께 확인하는 것이 좋습니다."
    else:
        keywords = _extract_keywords(content_text)
        topic = _infer_topic(keywords)
        first = f"{topic} 관련 주요 업데이트가 공유되었습니다."
        second = "변경된 기능과 실제 적용 시 영향 범위를 중심으로 핵심 포인트를 정리했습니다."
        third = "기술 선택과 우선순위에 영향을 줄 수 있으므로 팀 단위 검토가 필요합니다."

    lines = [
        f"핵심 요약 1: {first}",
        f"핵심 요약 2: {second}",
        f"왜 중요한가: {third}",
        "실무 적용: 영향 받는 서비스와 기능 플래그를 먼저 식별한 뒤 스테이징에서 회귀 테스트를 권장합니다.",
        "세부 포인트: 변경 전후 지표(지연 시간, 오류율, 비용)를 같은 조건에서 비교해 검증하세요.",
    ]
    return SummaryResult(lines=lines, ok=True)
