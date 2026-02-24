from __future__ import annotations

import base64

from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse

router = APIRouter(tags=["redirect"])


def encode_redirect_token(url: str) -> str:
    return base64.urlsafe_b64encode(url.encode("utf-8")).decode("utf-8")


def resolve_redirect_token(token: str) -> str:
    try:
        raw = base64.urlsafe_b64decode(token.encode("utf-8")).decode("utf-8")
    except Exception as exc:  # noqa: BLE001
        raise ValueError("invalid token") from exc
    if not raw.startswith("http"):
        raise ValueError("invalid target")
    return raw


@router.get("/r/{token}")
def redirect(token: str):
    try:
        target = resolve_redirect_token(token)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="invalid_redirect") from exc
    return RedirectResponse(url=target, status_code=302)
