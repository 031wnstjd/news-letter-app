from newsletter_api.newsletter.pipeline import _rank


def test_rank_prefers_geeknews_like_sources_over_heavy_research():
    base = {
        "age_hours": 3,
        "trust_tier": "T1",
        "summary": "테스트 요약",
        "title": "테스트 제목",
    }
    candidates = [
        {**base, "source_domain": "arxiv.org", "url": "https://arxiv.org/abs/1234.5678"},
        {**base, "source_domain": "news.hada.io", "url": "https://news.hada.io/topic?id=1"},
    ]

    ranked = _rank(candidates)
    assert ranked[0]["source_domain"] == "news.hada.io"
