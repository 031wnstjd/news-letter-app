from __future__ import annotations

from celery import chain

from .celery_app import celery_app


@celery_app.task(name="ingest")
def ingest() -> dict:
    return {"ok": True}


@celery_app.task(name="dedup")
def dedup(payload: dict) -> dict:
    return payload


@celery_app.task(name="rank")
def rank(payload: dict) -> dict:
    return payload


@celery_app.task(name="summarize")
def summarize(payload: dict) -> dict:
    return payload


@celery_app.task(name="verify")
def verify(payload: dict) -> dict:
    return payload


@celery_app.task(name="link_check")
def link_check(payload: dict) -> dict:
    return payload


@celery_app.task(name="compose")
def compose(payload: dict) -> dict:
    return payload


@celery_app.task(name="send")
def send(payload: dict) -> dict:
    return payload


def run_daily_chain() -> None:
    workflow = chain(
        ingest.s(),
        dedup.s(),
        rank.s(),
        summarize.s(),
        verify.s(),
        link_check.s(),
        compose.s(),
        send.s(),
    )
    workflow.delay()
