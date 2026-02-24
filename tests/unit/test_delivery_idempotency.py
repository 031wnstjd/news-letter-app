from newsletter_api.models import Delivery


def test_delivery_has_campaign_subscriber_unique_constraint():
    names = {c.name for c in Delivery.__table__.constraints if getattr(c, "name", None)}
    assert "uq_delivery_campaign_subscriber" in names
