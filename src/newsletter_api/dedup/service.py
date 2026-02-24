from __future__ import annotations

import re


def simple_similarity(a: str, b: str) -> float:
    tokens_a = set(re.findall(r"[a-z0-9]+", a.lower()))
    tokens_b = set(re.findall(r"[a-z0-9]+", b.lower()))
    if not tokens_a and not tokens_b:
        return 1.0
    if not tokens_a or not tokens_b:
        return 0.0
    inter = len(tokens_a & tokens_b)
    union = len(tokens_a | tokens_b)
    return inter / union


def should_merge(title_a: str, title_b: str, threshold: float = 0.86) -> bool:
    return simple_similarity(title_a, title_b) >= threshold


def should_merge_by_mixed_rule(
    canonical_url_a: str,
    canonical_url_b: str,
    title_a: str,
    title_b: str,
    entity_match: bool,
    threshold: float = 0.86,
) -> bool:
    if canonical_url_a == canonical_url_b:
        return True
    if not entity_match:
        return False
    return should_merge(title_a, title_b, threshold=threshold)
