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
            return SummaryResult(lines=[], ok=False, error="OPENAI_API_KEY is missing")
        if not source_text.strip():
            return SummaryResult(lines=[], ok=False, error="source_text is empty")

        prompt = (
            "Return strict JSON with keys: "
            "tldr(list of 2 short strings), why_it_matters(string), practical_apply(string).\\n"
            f"Title: {title}\\nURL: {url}\\nContent:\\n{source_text[:5000]}"
        )
        payload = {
            "model": self.model,
            "temperature": 0.2,
            "messages": [
                {"role": "system", "content": "You summarize technical news in Korean, concise and factual."},
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
                return SummaryResult(lines=[], ok=False, error="model returned empty summary")
            return SummaryResult(lines=lines, ok=True)
        except Exception as exc:  # noqa: BLE001
            return SummaryResult(lines=[], ok=False, error=f"openai request failed: {exc}")
        finally:
            if own_client:
                client.close()


def summarize_text(text: str) -> SummaryResult:
    if not text.strip():
        return SummaryResult(lines=[], ok=False, error="source_text is empty")
    # Stubbed deterministic summary for MVP scaffolding.
    lines = [
        text.strip().split(". ")[0][:160],
        "Why it matters: practical impact for engineering teams.",
        "Apply: evaluate adoption in staging before production.",
    ]
    return SummaryResult(lines=lines, ok=True)
