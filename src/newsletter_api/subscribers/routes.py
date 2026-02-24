from pydantic import BaseModel
from fastapi import APIRouter, HTTPException

from .service import service

router = APIRouter(tags=["subscribers"])


class SubscribeIn(BaseModel):
    email: str


class SubscribeOut(BaseModel):
    email: str
    status: str
    verification_token: str


@router.post("/v1/subscribers", response_model=SubscribeOut, status_code=202)
def subscribe(payload: SubscribeIn) -> SubscribeOut:
    created = service.create_pending_subscriber(payload.email)
    return SubscribeOut(
        email=created.email,
        status=created.status,
        verification_token=created.verification_token,
    )


@router.post("/v1/subscribers/verify/{token}")
def verify(token: str) -> dict[str, str]:
    try:
        service.verify_subscriber(token)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="token_not_found") from exc
    return {"status": "verified"}
