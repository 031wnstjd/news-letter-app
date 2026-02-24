from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from newsletter_api.delivery.redirect import router as redirect_router
from newsletter_api.frontend.routes import router as frontend_router
from newsletter_api.newsletter.routes import router as newsletter_router
from newsletter_api.subscribers.routes import router as subscriber_router
from newsletter_api.summarization.routes import router as summarization_router

app = FastAPI(title="AI/Dev Daily Newsletter")
app.include_router(subscriber_router)
app.include_router(redirect_router)
app.include_router(newsletter_router)
app.include_router(summarization_router)
app.include_router(frontend_router)

_STATIC_DIR = Path(__file__).resolve().parents[2] / "static"
app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
