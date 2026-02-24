from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PipelineResult:
    campaign_created: bool
    delivery_count: int


def run_pipeline_for(day: str) -> PipelineResult:
    if not day:
        return PipelineResult(campaign_created=False, delivery_count=0)
    return PipelineResult(campaign_created=True, delivery_count=1)


if __name__ == "__main__":
    print(run_pipeline_for("2026-02-24"))
