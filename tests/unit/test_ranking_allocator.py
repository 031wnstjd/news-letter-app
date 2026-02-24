from newsletter_api.ranking.allocator import allocate_slots


def sample_candidates() -> list[dict]:
    return [
        {"score": 99, "category": "LLM/Agent", "age_hours": 3},
        {"score": 98, "category": "Backend", "age_hours": 6},
        {"score": 97, "category": "Frontend", "age_hours": 7},
        {"score": 96, "category": "Infra/MLOps", "age_hours": 10},
        {"score": 95, "category": "Data", "age_hours": 20},
        {"score": 94, "category": "Security", "age_hours": 22},
        {"score": 93, "category": "LLM/Agent", "age_hours": 30},
        {"score": 92, "category": "Backend", "age_hours": 36},
    ]


def test_allocate_slots_has_2_hot_and_6_bottom():
    selected = allocate_slots(sample_candidates())
    assert len(selected.hot) == 2
    assert len(selected.bottom) == 6
