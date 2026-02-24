# Ranking Model (MVP v1)

## 1) Core Formula

```text
base_score =
  0.20 * recency_score +
  0.40 * authority_score +
  0.30 * impact_score -
  0.10 * commercial_penalty
```

## 2) Time Windows

- Dual-window allocation for final 8 items:
  - Fast window (0~24h): 60%
  - Verified window (24~96h): 40%

## 3) Community Signal Rules

- Community boost is applied only to `impact_score`.
- Boost cap: max `+15%` of total score.
- If no primary source is detected, community boost is reduced by `50%`.
- Community boost half-life: `48h`.

## 4) Source Diversity Rules

- Max 3 items per same organization per campaign.
- Overflow items are downgraded to additional reads.

## 5) Commerciality Rules

- Strong commercial penalty is enabled by default.
- Exception: if both conditions are met, penalty is reduced by 50%:
  - official technical documentation exists
  - reproducible code exists

## 6) Slot Allocation Rules

- Top slots: 2 hot issues
  - must be different categories
- Bottom slots: 6 items
  - at least 4 categories covered
  - remaining slots by score order
- Hybrid fallback:
  - relax lower threshold only until minimum 3 items are secured

## 7) Dedup Interaction

- Dedup runs before ranking.
- Merge conditions:
  - canonical URL match, or
  - semantic similarity threshold `0.86` with entity alignment
