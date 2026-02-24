from __future__ import annotations


def filter_unverified_claims(lines: list[str], verification: dict[str, bool]) -> list[str]:
    return [line for line in lines if verification.get(line, False)]
