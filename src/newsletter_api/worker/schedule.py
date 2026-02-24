from __future__ import annotations

from datetime import datetime


def should_send_now(iso_dt: str) -> bool:
    dt = datetime.fromisoformat(iso_dt)
    return dt.weekday() < 5 and dt.hour == 9 and dt.minute == 0
