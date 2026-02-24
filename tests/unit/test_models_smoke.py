from newsletter_api.models import Item, Source, Subscriber


def test_model_tables_are_named():
    assert Source.__tablename__ == "sources"
    assert Item.__tablename__ == "items"
    assert Subscriber.__tablename__ == "subscribers"
