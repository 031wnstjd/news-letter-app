from __future__ import annotations


def score(recency: float, authority: float, impact: float, commercial_penalty: float) -> float:
    return (
        0.20 * recency
        + 0.40 * authority
        + 0.30 * impact
        - 0.10 * commercial_penalty
    )
