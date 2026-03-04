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
        timeout: float = 35.0,
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
        headers = {"Authorization": f"Bearer {self.api_key}"}

        own_client = self.client is None
        client = self.client or httpx.Client(timeout=self.timeout)
        last_error = "OpenAI 요청에 실패했습니다."
        try:
            for max_chars in (3200, 1600):
                prompt = (
                    "반드시 JSON 객체로만 응답하세요. 키는 정확히 다음 8개만 사용하세요: "
                    "translated_title(string), lead(string), what_happened(array[string] 길이 3~5), "
                    "key_facts(array[string] 길이 5~8), why_it_matters(array[string] 길이 2~4), "
                    "practical_steps(array[string] 길이 3~5), caveats(array[string] 길이 2~3), "
                    "source_notes(array[string] 길이 2~4). "
                    "모든 값은 한국어로 작성하고 영어 문장을 그대로 복사하지 말고 한국어로 의역하세요. "
                    "문체는 논문 초록처럼 무겁지 않게, 기술 커뮤니티 브리핑 스타일로 작성하세요. "
                    "사용자는 원문 링크를 보지 않는다고 가정하고 맥락과 실행 포인트를 충분히 담아주세요.\\n"
                    f"원문 제목: {title}\\n원문 URL: {url}\\n원문 내용:\\n{source_text[:max_chars]}"
                )
                payload = {
                    "model": self.model,
                    "temperature": 0.2,
                    "max_tokens": 900,
                    "response_format": {"type": "json_object"},
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

                try:
                    response = client.post(f"{self.base_url}/chat/completions", json=payload, headers=headers)
                    response.raise_for_status()
                    content = str(response.json()["choices"][0]["message"].get("content", "")).strip()
                    parsed = _parse_json_from_content(content)
                    if parsed is None:
                        rescued = _build_lines_from_ai_text(content)
                        if rescued:
                            return SummaryResult(lines=rescued, ok=True, translated_title=title)
                        last_error = "OpenAI 응답 파싱에 실패했습니다."
                        continue

                    lead = str(parsed.get("lead", "")).strip()

                    def _normalize_list(value: object) -> list[str]:
                        if isinstance(value, str):
                            value = [value]
                        if not isinstance(value, list):
                            return []
                        return [str(item).strip() for item in value if str(item).strip()]

                    what_happened = _normalize_list(parsed.get("what_happened"))[:5]
                    key_facts = _normalize_list(parsed.get("key_facts"))[:8]
                    why_it_matters = _normalize_list(parsed.get("why_it_matters"))[:4]
                    practical_steps = _normalize_list(parsed.get("practical_steps"))[:5]
                    caveats = _normalize_list(parsed.get("caveats"))[:3]
                    source_notes = _normalize_list(parsed.get("source_notes"))[:4]

                    lines: list[str] = []
                    if lead:
                        lines.append(f"리드: {lead}")
                    lines.extend(f"무엇이 나왔나: {point}" for point in what_happened)
                    lines.extend(f"핵심 사실: {point}" for point in key_facts)
                    lines.extend(f"중요한 이유: {point}" for point in why_it_matters)
                    lines.extend(f"실무 적용: {point}" for point in practical_steps)
                    lines.extend(f"주의사항: {point}" for point in caveats)
                    lines.extend(f"출처 메모: {point}" for point in source_notes)
                    lines = [line.strip() for line in lines if line and line.strip()]
                    if not lines:
                        last_error = "모델이 비어 있는 요약을 반환했습니다."
                        continue
                    translated_title = str(parsed.get("translated_title", "")).strip()
                    return SummaryResult(lines=lines, ok=True, translated_title=translated_title)
                except httpx.TimeoutException:
                    last_error = "OpenAI 응답 시간이 초과되었습니다."
                    continue
                except httpx.HTTPStatusError as exc:
                    status = exc.response.status_code if exc.response is not None else "unknown"
                    last_error = f"OpenAI HTTP 오류({status})"
                    continue
                except Exception:  # noqa: BLE001
                    last_error = "OpenAI 요청에 실패했습니다."
                    continue

            return SummaryResult(lines=[], ok=False, error=last_error)
        finally:
            if own_client:
                client.close()


_WS_RE = re.compile(r"\s+")
_SENTENCE_RE = re.compile(r"(?<=[.!?。！？])\s+")
_SECTION_HEADER_RE = re.compile(r"\[[^\]]+\]")
_HANGUL_RE = re.compile(r"[가-힣]")
_LATIN_RE = re.compile(r"[A-Za-z]")
_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9+._/-]{2,}|[가-힣]{2,}")
_NOISE_SENTENCE_RE = re.compile(
    r"(?:^posted on\b|read more\b|comments?\b|share\b|subscribe\b|sign in\b|all rights reserved\b)",
    re.IGNORECASE,
)
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


def _pick_sentences(text: str, max_items: int = 12) -> list[str]:
    normalized = _WS_RE.sub(" ", text).strip()
    normalized = _SECTION_HEADER_RE.sub(" ", normalized)
    parts = [p.strip() for p in _SENTENCE_RE.split(normalized) if p.strip()]
    parts = [p for p in parts if len(p) >= 18]
    if parts:
        return parts[:max_items]

    if not normalized:
        return []

    chunked = []
    cursor = 0
    while cursor < len(normalized) and len(chunked) < max_items:
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


def _parse_json_from_content(content: str) -> dict | None:
    text = content.strip()
    if not text:
        return None
    if text.startswith("```"):
        lines = text.splitlines()
        if len(lines) >= 3 and lines[0].startswith("```"):
            text = "\n".join(lines[1:-1]).strip()
            if text.lower().startswith("json"):
                text = text[4:].strip()
    try:
        parsed = json.loads(text)
        return parsed if isinstance(parsed, dict) else None
    except Exception:  # noqa: BLE001
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or start >= end:
        return None
    try:
        parsed = json.loads(text[start : end + 1])
        return parsed if isinstance(parsed, dict) else None
    except Exception:  # noqa: BLE001
        return None


def _build_lines_from_ai_text(content: str) -> list[str]:
    cleaned = _WS_RE.sub(" ", content).strip()
    if not cleaned:
        return []
    parts = [p.strip(" -•") for p in re.split(r"(?:\n+|(?<=[.!?。！？])\s+)", content) if p.strip()]
    parts = [p for p in parts if len(p) >= 8]
    lead = _truncate(parts[0]) if parts else _truncate(cleaned)
    what = [_truncate(p) for p in parts[1:4]]
    facts = [_truncate(p) for p in parts[4:10]]
    if not what:
        what = ["모델 응답에서 변경 사항을 추출해 정리했습니다."]
    if not facts:
        facts = ["핵심 사실을 자동 추출해 카드 형식으로 재구성했습니다."]
    lines = [f"리드: {lead}"]
    lines.extend(f"무엇이 나왔나: {point}" for point in what)
    lines.extend(f"핵심 사실: {point}" for point in facts)
    lines.append("중요한 이유: 해당 변경은 팀의 기술 선택과 운영 우선순위에 직접 영향을 줍니다.")
    lines.append("실무 적용: 현재 워크플로에 미치는 영향을 작은 범위에서 먼저 검증하세요.")
    lines.append("주의사항: 세부 조건과 예외 케이스는 운영 환경에서 다르게 나타날 수 있습니다.")
    lines.append("출처 메모: 모델의 자유 서술 응답을 카드 양식에 맞춰 재구성했습니다.")
    return lines


def _find_first_matching_sentence(sentences: list[str], keywords: tuple[str, ...], default: str) -> str:
    lowered_keywords = tuple(keyword.lower() for keyword in keywords)
    for sentence in sentences:
        lowered = sentence.lower()
        if any(keyword in lowered for keyword in lowered_keywords):
            return _truncate(sentence)
    return default


def _is_noise_sentence(sentence: str) -> bool:
    compact = _WS_RE.sub(" ", sentence).strip()
    if len(compact) < 18:
        return True
    lowered = compact.lower()
    if _NOISE_SENTENCE_RE.search(lowered):
        return True
    if lowered.startswith(("posted on ", "read more", "comments", "share ")):
        return True
    return False


def _dedup_preserve(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        key = value.strip()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(key)
    return out


def _sentence_score(sentence: str) -> float:
    lowered = sentence.lower()
    score = 0.0
    if re.search(r"\d", sentence):
        score += 2.0
    if re.search(r"[A-Z][a-z]+", sentence):
        score += 0.8
    if any(token in lowered for token in ("launch", "release", "announce", "support", "improve", "reduce", "increase", "timeline", "session", "prompt", "file", "api", "mcp", "npm", "download")):
        score += 1.2
    score += min(len(sentence) / 180.0, 1.0)
    return score


def _select_grounded_sentences(sentences: list[str], limit: int, prefer_numeric: bool = False) -> list[str]:
    if not sentences:
        return []
    indexed = list(enumerate(sentences))
    if prefer_numeric:
        numeric = [pair for pair in indexed if re.search(r"\d", pair[1])]
        if numeric:
            indexed = numeric
    ranked = sorted(indexed, key=lambda pair: _sentence_score(pair[1]), reverse=True)[:limit]
    selected_indexes = sorted(index for index, _ in ranked)
    return [sentences[index] for index in selected_indexes]


def _grounded_line(sentence: str) -> str:
    compact = _truncate(_WS_RE.sub(" ", sentence).strip(), 200)
    if not compact:
        return ""
    if _is_korean_dominant(compact):
        return compact
    return f"원문 근거: {compact}"


def summarize_text(text: str) -> SummaryResult:
    if not text.strip():
        return SummaryResult(lines=[], ok=False, error="요약할 본문이 비어 있습니다.")
    content_text = _SECTION_HEADER_RE.sub(" ", text)
    content_text = _WS_RE.sub(" ", content_text).strip()

    if _is_korean_dominant(content_text):
        sentences = _pick_sentences(content_text, max_items=16)
        lead = _truncate(sentences[0]) if len(sentences) > 0 else "이번 업데이트의 핵심 흐름을 빠르게 정리했습니다."
        what_happened = [_truncate(sentence) for sentence in sentences[1:5]]
        key_facts = [_truncate(sentence) for sentence in sentences[5:13]]
        why_points = [
            _find_first_matching_sentence(
                sentences,
                ("영향", "효율", "성능", "비용", "확장", "안정성"),
                "기술 선택과 우선순위에 영향을 주기 때문에 팀 단위 판단이 필요합니다.",
            ),
            "단기 적용성뿐 아니라 운영 안정성과 유지보수 비용까지 함께 검토해야 합니다.",
        ]
        practical = _find_first_matching_sentence(
            sentences,
            ("적용", "운영", "테스트", "검증", "배포", "설정"),
            "변경 전후 지표를 비교할 수 있도록 스테이징에서 검증 절차를 먼저 준비하세요.",
        )
        risk_points = [
            _find_first_matching_sentence(
                sentences,
                ("주의", "문제", "한계", "리스크", "위험", "실패", "오류"),
                "초기 적용 단계에서 예상과 다른 동작이 발생할 수 있으므로 점진 적용이 필요합니다.",
            ),
            "서비스 영향도가 큰 구간은 모니터링 지표와 롤백 기준을 미리 정의하세요.",
        ]
        practical_steps = [
            practical,
            "변경 대상 기능과 의존 시스템 목록을 먼저 정리하세요.",
            "스테이징에서 대표 시나리오 기준의 회귀 테스트를 실행하세요.",
            "배포 후 오류율·지연 시간·비용 지표를 최소 하루 이상 추적하세요.",
        ]
        source_notes = ["기사 원문에서 제시한 기능/정책 변경 범위를 기준으로 정리했습니다."]
    else:
        keywords = _extract_keywords(content_text, limit=6)
        topic = _infer_topic(keywords)
        raw_sentences = _pick_sentences(content_text, max_items=24)
        sentences = [sentence for sentence in raw_sentences if not _is_noise_sentence(sentence)]
        sentences = _dedup_preserve(sentences)

        if not sentences:
            lead = f"{topic} 관련 업데이트를 수집했지만 본문 문장 추출이 제한되어 핵심 신호 중심으로 정리했습니다."
            what_happened = [f"{topic}와 관련된 변경이 감지되었습니다."]
            key_facts = [f"원문 텍스트 길이: {len(content_text)}자 (문장 추출 실패)"]
        else:
            lead_keywords = ", ".join(keywords[:3]) if keywords else topic
            lead = f"{topic} 관련 업데이트입니다. 원문 문장 기반으로 핵심을 정리했습니다 ({lead_keywords})."
            what_candidates = _select_grounded_sentences(sentences, limit=5, prefer_numeric=False)
            fact_candidates = _select_grounded_sentences(sentences, limit=8, prefer_numeric=True)
            combined = _dedup_preserve([*fact_candidates, *what_candidates, *sentences])
            what_happened = [_grounded_line(sentence) for sentence in what_candidates[:5]]
            key_facts = [_grounded_line(sentence) for sentence in combined[:8]]
            what_happened = [line for line in what_happened if line]
            key_facts = [line for line in key_facts if line]

        impact_sentence = _find_first_matching_sentence(
            sentences,
            ("improv", "reduc", "increase", "support", "timeline", "session", "deploy", "latency", "cost"),
            "원문에서 성능·운영 방식에 영향을 주는 변경이 명시되었습니다.",
        )
        why_points = [
            f"기사에서 도입 효과/변경 지점이 직접 언급됩니다: {_grounded_line(impact_sentence)}",
            "원문 근거 문장을 기준으로 우선순위를 정하면 과장된 해석을 줄일 수 있습니다.",
        ]

        first_fact = key_facts[0] if key_facts else "원문 핵심 문장을 먼저 검토하세요."
        second_fact = key_facts[1] if len(key_facts) > 1 else first_fact
        practical_steps = [
            f"아래 핵심 사실 1순위를 검증하세요: {first_fact}",
            f"핵심 사실 간 충돌 여부를 확인하세요: {second_fact}",
            "도입 전후로 성능/안정성/운영비용 지표를 같은 조건에서 비교하세요.",
            "원문의 수치·버전·일정을 사내 기준 문서에 옮길 때 출처 링크를 함께 남기세요.",
        ]
        risk_points = [
            "영문 원문을 한국어로 옮길 때 용어가 달라질 수 있으니 고유명사와 수치는 원문 그대로 재검증하세요.",
            "요약 문장만으로 의사결정하지 말고, 영향이 큰 항목은 반드시 원문 맥락(앞뒤 문단)까지 확인하세요.",
        ]
        source_notes = [
            f"원문에서 추출한 문장 {len(sentences)}개를 기반으로 정보량이 높은 순서로 재구성했습니다.",
            "모델 응답 실패 시에도 원문 근거 문장을 우선 유지하도록 설계했습니다.",
        ]

    if not what_happened:
        what_happened = ["이번 업데이트에서 변경된 핵심 항목을 우선 정리했습니다."]
    if not key_facts:
        key_facts = ["변경 사항의 실제 영향 범위를 중심으로 핵심 사실을 재구성했습니다."]

    lines = [f"리드: {lead}"]
    lines.extend(f"무엇이 나왔나: {point}" for point in what_happened[:5])
    lines.extend(f"핵심 사실: {point}" for point in key_facts[:8])
    lines.extend(f"중요한 이유: {point}" for point in why_points[:4])
    lines.extend(f"실무 적용: {point}" for point in practical_steps[:5])
    lines.extend(f"주의사항: {risk}" for risk in risk_points[:3])
    lines.extend(f"출처 메모: {note}" for note in source_notes[:4])
    return SummaryResult(lines=lines, ok=True)
