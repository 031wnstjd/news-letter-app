from __future__ import annotations

from celery import Celery

from newsletter_api.config import Settings

settings = Settings()

celery_app = Celery(
    "newsletter_worker",
    broker=settings.redis_url,
    backend=settings.redis_url,
)
celery_app.conf.timezone = "Asia/Seoul"
celery_app.conf.enable_utc = False
