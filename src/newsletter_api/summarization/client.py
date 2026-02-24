from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SummaryResult:
    lines: list[str]
    ok: bool


def summarize_text(text: str) -> SummaryResult:
    if not text.strip():
        return SummaryResult(lines=[], ok=False)
    # Stubbed deterministic summary for MVP scaffolding.
    lines = [
        text.strip().split(". ")[0][:160],
        "Why it matters: practical impact for engineering teams.",
        "Apply: evaluate adoption in staging before production.",
    ]
    return SummaryResult(lines=lines, ok=True)
