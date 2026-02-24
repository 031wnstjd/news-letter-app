from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from secrets import token_urlsafe


@dataclass
class SubscriberRecord:
    email: str
    status: str
    verification_token: str
    created_at: datetime
    verified_at: datetime | None = None


SUBSCRIBERS: dict[str, SubscriberRecord] = {}
TOKEN_INDEX: dict[str, str] = {}


class SubscriberService:
    def create_pending_subscriber(self, email: str) -> SubscriberRecord:
        token = token_urlsafe(24)
        record = SubscriberRecord(
            email=email,
            status="pending",
            verification_token=token,
            created_at=datetime.now(tz=timezone.utc),
        )
        SUBSCRIBERS[email] = record
        TOKEN_INDEX[token] = email
        return record

    def verify_subscriber(self, token: str) -> SubscriberRecord:
        email = TOKEN_INDEX.get(token)
        if not email:
            raise ValueError("invalid token")
        record = SUBSCRIBERS[email]
        record.status = "verified"
        record.verified_at = datetime.now(tz=timezone.utc)
        return record


service = SubscriberService()
