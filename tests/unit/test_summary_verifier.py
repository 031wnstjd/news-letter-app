from newsletter_api.summarization.verify import filter_unverified_claims


def test_filter_unverified_claims_removes_mismatch_sentence():
    summary = ["A", "B"]
    verified = {"A": True, "B": False}
    assert filter_unverified_claims(summary, verified) == ["A"]
