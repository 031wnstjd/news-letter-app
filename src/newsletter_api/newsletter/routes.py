from fastapi import APIRouter

from .pipeline import build_daily_newsletter

router = APIRouter(prefix="/v1/newsletter", tags=["newsletter"])


@router.get("/preview")
def preview(limit: int = 8) -> dict:
    return build_daily_newsletter(limit=limit)
