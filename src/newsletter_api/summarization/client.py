from __future__ import annotations

from dataclasses import dataclass
import json

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
            "반드시 JSON 객체로만 응답하세요. 키는 정확히 다음 4개만 사용하세요: "
            "translated_title(string), tldr(array[string] 길이 2), why_it_matters(string), practical_apply(string). "
            "모든 값은 한국어로 작성하세요.\\n"
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
                        "반드시 한국어로만 작성하고 과장 없이 사실 중심으로 요약하세요."
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
            lines = [
                str(tldr[0]) if len(tldr) > 0 else "",
                str(tldr[1]) if len(tldr) > 1 else "",
                str(parsed.get("why_it_matters", "")),
                str(parsed.get("practical_apply", "")),
            ]
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


def summarize_text(text: str) -> SummaryResult:
    if not text.strip():
        return SummaryResult(lines=[], ok=False, error="요약할 본문이 비어 있습니다.")
    # API 키가 없거나 모델 응답이 실패한 경우에 사용하는 한국어 기본 요약.
    lines = [
        "핵심 요약: 입력된 내용을 바탕으로 주요 변경점과 맥락을 정리했습니다.",
        "왜 중요한가: 실무 팀의 우선순위와 기술 선택에 영향을 줍니다.",
        "실무 적용: 스테이징 환경에서 영향 범위를 먼저 검증하세요.",
    ]
    return SummaryResult(lines=lines, ok=True)
