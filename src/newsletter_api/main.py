from fastapi import FastAPI

from newsletter_api.delivery.redirect import router as redirect_router
from newsletter_api.subscribers.routes import router as subscriber_router

app = FastAPI(title="AI/Dev Daily Newsletter")
app.include_router(subscriber_router)
app.include_router(redirect_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
