from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass


@dataclass
class AllocationResult:
    hot: list[dict]
    bottom: list[dict]


def _split_windows(candidates: list[dict]) -> tuple[list[dict], list[dict]]:
    fast = [c for c in candidates if c.get("age_hours", 9999) <= 24]
    verified = [c for c in candidates if 24 < c.get("age_hours", 9999) <= 96]
    return fast, verified


def allocate_slots(candidates: list[dict]) -> AllocationResult:
    ordered = sorted(candidates, key=lambda x: x["score"], reverse=True)
    hot: list[dict] = []
    used_hot_categories: set[str] = set()
    for item in ordered:
        category = item.get("category", "unknown")
        if category in used_hot_categories:
            continue
        hot.append(item)
        used_hot_categories.add(category)
        if len(hot) == 2:
            break

    remaining = [i for i in ordered if i not in hot]
    fast, verified = _split_windows(remaining)
    target_fast = 4
    target_verified = 2

    bottom: list[dict] = fast[:target_fast] + verified[:target_verified]
    if len(bottom) < 6:
        for item in remaining:
            if item not in bottom:
                bottom.append(item)
            if len(bottom) == 6:
                break

    # Ensure at least 4 categories in bottom slots if possible.
    cat_counts = defaultdict(int)
    for item in bottom:
        cat_counts[item.get("category", "unknown")] += 1
    if len(cat_counts) < 4:
        for candidate in remaining:
            c = candidate.get("category", "unknown")
            if c in cat_counts:
                continue
            for idx, existing in enumerate(bottom):
                ecat = existing.get("category", "unknown")
                if cat_counts[ecat] > 1:
                    cat_counts[ecat] -= 1
                    bottom[idx] = candidate
                    cat_counts[c] += 1
                    break
            if len(cat_counts) >= 4:
                break

    return AllocationResult(hot=hot[:2], bottom=bottom[:6])
