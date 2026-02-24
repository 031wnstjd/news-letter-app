from scripts.run_daily_pipeline import run_pipeline_for


def test_daily_campaign_pipeline_generates_campaign_and_deliveries():
    result = run_pipeline_for("2026-02-24")
    assert result.campaign_created is True
    assert result.delivery_count > 0
