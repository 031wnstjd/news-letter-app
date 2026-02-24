from newsletter_api.worker.schedule import should_send_now


def test_should_send_now_for_weekday_0900_kst():
    assert should_send_now("2026-02-24T09:00:00+09:00") is True
    assert should_send_now("2026-02-24T09:01:00+09:00") is False
