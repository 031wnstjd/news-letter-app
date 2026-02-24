from __future__ import annotations

from dataclasses import dataclass

import httpx

from newsletter_api.config import Settings


@dataclass
class SendResult:
    accepted: bool
    provider_message_id: str | None


class ResendClient:
    base_url = "https://api.resend.com"

    def __init__(self) -> None:
        self.settings = Settings()

    def send(self, to_email: str, subject: str, html: str, text: str) -> SendResult:
        payload = {
            "from": self.settings.resend_from_email,
            "to": [to_email],
            "subject": subject,
            "html": html,
            "text": text,
        }
        headers = {"Authorization": f"Bearer {self.settings.resend_api_key}"}
        with httpx.Client(timeout=10.0) as client:
            response = client.post(f"{self.base_url}/emails", json=payload, headers=headers)
        if response.status_code >= 400:
            return SendResult(accepted=False, provider_message_id=None)
        data = response.json()
        return SendResult(accepted=True, provider_message_id=data.get("id"))
