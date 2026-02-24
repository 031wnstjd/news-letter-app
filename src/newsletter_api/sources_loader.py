from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class SourceGroups:
    official: list[dict]
    community: list[dict]


def load_sources(path: str | Path) -> SourceGroups:
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    return SourceGroups(
        official=raw["sources"]["official"],
        community=raw["sources"]["community"],
    )
