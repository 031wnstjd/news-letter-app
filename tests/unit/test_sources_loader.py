from newsletter_api.sources_loader import load_sources


def test_load_sources_returns_official_and_community():
    data = load_sources("sources.yaml")
    assert len(data.official) == 10
    assert len(data.community) == 11
