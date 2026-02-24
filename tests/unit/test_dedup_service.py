from newsletter_api.dedup.service import should_merge


def test_should_merge_when_similarity_above_threshold():
    assert should_merge("A new GPT release", "A new GPT release", 0.86) is True
