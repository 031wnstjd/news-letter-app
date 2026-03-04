from __future__ import annotations

import json
from queue import Queue
import threading

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from .pipeline import build_daily_newsletter

router = APIRouter(prefix="/v1/newsletter", tags=["newsletter"])


@router.get("/preview")
def preview(limit: int = 8) -> dict:
    return build_daily_newsletter(limit=limit)


@router.get("/preview/stream")
def preview_stream(limit: int = 8) -> StreamingResponse:
    event_queue: Queue[dict | object] = Queue()
    sentinel = object()

    def run_worker() -> None:
        try:
            result = build_daily_newsletter(limit=limit, progress_callback=event_queue.put)
            event_queue.put({"event": "done", "payload": result})
        except Exception as exc:  # noqa: BLE001
            event_queue.put({"event": "failed", "payload": {"message": "프리뷰 생성 실패", "detail": str(exc)}})
        finally:
            event_queue.put(sentinel)

    thread = threading.Thread(target=run_worker, daemon=True)
    thread.start()

    def event_generator():
        yield ": connected\n\n"
        while True:
            item = event_queue.get()
            if item is sentinel:
                break
            if not isinstance(item, dict):
                continue
            if item.get("event") in {"done", "failed"}:
                event_name = item["event"]
                payload = item["payload"]
            else:
                event_name = "progress"
                payload = item
            yield f"event: {event_name}\n"
            yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
