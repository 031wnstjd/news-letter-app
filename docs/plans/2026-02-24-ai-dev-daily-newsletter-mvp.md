# AI/Dev Daily Newsletter MVP Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build the production-ready MVP defined in `FINAL_SPEC.md` with deterministic 09:00 KST weekday delivery, 8-item selection, and reliable subscription/delivery pipeline.

**Architecture:** A FastAPI app handles APIs and campaign composition, Celery workers execute ingestion/ranking/summarization/delivery jobs, Redis is the broker, and Postgres stores source/item/ranking/subscriber/delivery records. Daily scheduling builds one campaign, validates links, and sends via Resend with idempotent delivery guarantees.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy, Alembic, Celery, Redis, Postgres, Jinja2, httpx, pytest, pytest-asyncio, Docker Compose.

---

## Execution Notes

- Skill refs: `@test-driven-development`, `@verification-before-completion`
- Keep each commit scoped to one task.
- Do not add behavior not described in `FINAL_SPEC.md`.

### Task 1: Bootstrap Service Skeleton

**Files:**
- Create: `pyproject.toml`
- Create: `src/newsletter_api/__init__.py`
- Create: `src/newsletter_api/main.py`
- Create: `tests/api/test_healthcheck.py`

**Step 1: Write the failing test**

```python
from fastapi.testclient import TestClient
from newsletter_api.main import app


def test_healthcheck_returns_ok():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/api/test_healthcheck.py -v`  
Expected: FAIL with `ModuleNotFoundError: No module named 'newsletter_api'`

**Step 3: Write minimal implementation**

```python
# src/newsletter_api/main.py
from fastapi import FastAPI

app = FastAPI(title="AI/Dev Daily Newsletter")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/api/test_healthcheck.py -v`  
Expected: PASS

**Step 5: Commit**

```bash
git add pyproject.toml src/newsletter_api/__init__.py src/newsletter_api/main.py tests/api/test_healthcheck.py
git commit -m "chore: bootstrap fastapi service with health endpoint"
```

### Task 2: Add Configuration and Settings

**Files:**
- Create: `src/newsletter_api/config.py`
- Modify: `src/newsletter_api/main.py`
- Create: `tests/unit/test_config.py`

**Step 1: Write the failing test**

```python
import os
from newsletter_api.config import Settings


def test_settings_loads_required_env(monkeypatch):
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/newsletter")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setenv("RESEND_API_KEY", "re_test")
    settings = Settings()
    assert settings.app_env == "test"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_config.py -v`  
Expected: FAIL with import error for `newsletter_api.config`

**Step 3: Write minimal implementation**

```python
# src/newsletter_api/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    app_env: str = "dev"
    database_url: str
    redis_url: str
    resend_api_key: str
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_config.py -v`  
Expected: PASS

**Step 5: Commit**

```bash
git add src/newsletter_api/config.py src/newsletter_api/main.py tests/unit/test_config.py
git commit -m "feat: add typed environment configuration"
```

### Task 3: Define Database Models and Migration Baseline

**Files:**
- Create: `src/newsletter_api/db.py`
- Create: `src/newsletter_api/models.py`
- Create: `alembic.ini`
- Create: `alembic/env.py`
- Create: `alembic/versions/20260224_0001_initial_tables.py`
- Create: `tests/unit/test_models_smoke.py`

**Step 1: Write the failing test**

```python
from newsletter_api.models import Source, Item, Subscriber


def test_model_tables_are_named():
    assert Source.__tablename__ == "sources"
    assert Item.__tablename__ == "items"
    assert Subscriber.__tablename__ == "subscribers"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_models_smoke.py -v`  
Expected: FAIL because models are missing

**Step 3: Write minimal implementation**

```python
# src/newsletter_api/models.py
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Source(Base):
    __tablename__ = "sources"
    id: Mapped[int] = mapped_column(primary_key=True)


class Item(Base):
    __tablename__ = "items"
    id: Mapped[int] = mapped_column(primary_key=True)


class Subscriber(Base):
    __tablename__ = "subscribers"
    id: Mapped[int] = mapped_column(primary_key=True)
```

Then expand these models to match `FINAL_SPEC.md` entities and create an Alembic initial migration.

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_models_smoke.py -v`  
Expected: PASS

**Step 5: Commit**

```bash
git add src/newsletter_api/db.py src/newsletter_api/models.py alembic.ini alembic/env.py alembic/versions/20260224_0001_initial_tables.py tests/unit/test_models_smoke.py
git commit -m "feat: add core sql models and initial migration"
```

### Task 4: Implement Source Registry Loader (`sources.yaml`)

**Files:**
- Create: `src/newsletter_api/sources_loader.py`
- Modify: `sources.yaml`
- Create: `tests/unit/test_sources_loader.py`

**Step 1: Write the failing test**

```python
from newsletter_api.sources_loader import load_sources


def test_load_sources_returns_official_and_community():
    data = load_sources("sources.yaml")
    assert len(data.official) == 10
    assert len(data.community) == 11
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_sources_loader.py -v`  
Expected: FAIL with missing loader

**Step 3: Write minimal implementation**

```python
import yaml
from dataclasses import dataclass


@dataclass
class SourceGroups:
    official: list[dict]
    community: list[dict]


def load_sources(path: str) -> SourceGroups:
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    return SourceGroups(
        official=raw["sources"]["official"],
        community=raw["sources"]["community"],
    )
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_sources_loader.py -v`  
Expected: PASS

**Step 5: Commit**

```bash
git add src/newsletter_api/sources_loader.py sources.yaml tests/unit/test_sources_loader.py
git commit -m "feat: add typed source registry loader"
```

### Task 5: Build Subscription + Double Opt-In Flow

**Files:**
- Create: `src/newsletter_api/subscribers/routes.py`
- Create: `src/newsletter_api/subscribers/service.py`
- Modify: `src/newsletter_api/main.py`
- Create: `tests/api/test_subscription_flow.py`

**Step 1: Write the failing test**

```python
from fastapi.testclient import TestClient
from newsletter_api.main import app


def test_subscribe_and_verify_flow():
    client = TestClient(app)
    create = client.post("/v1/subscribers", json={"email": "dev@example.com"})
    assert create.status_code == 202
    token = create.json()["verification_token"]
    verify = client.post(f"/v1/subscribers/verify/{token}")
    assert verify.status_code == 200
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/api/test_subscription_flow.py -v`  
Expected: FAIL because routes do not exist

**Step 3: Write minimal implementation**

```python
# route examples
@router.post("/v1/subscribers")
def subscribe(payload: SubscribeIn) -> SubscribeOut:
    return service.create_pending_subscriber(payload.email)


@router.post("/v1/subscribers/verify/{token}")
def verify(token: str) -> dict[str, str]:
    service.verify_subscriber(token)
    return {"status": "verified"}
```

Include queue-status notification email trigger for waitlisted users.

**Step 4: Run test to verify it passes**

Run: `pytest tests/api/test_subscription_flow.py -v`  
Expected: PASS

**Step 5: Commit**

```bash
git add src/newsletter_api/subscribers/routes.py src/newsletter_api/subscribers/service.py src/newsletter_api/main.py tests/api/test_subscription_flow.py
git commit -m "feat: implement subscriber double opt-in endpoints"
```

### Task 6: Implement Ingestion Pipeline (RSS Primary, HTML Fallback)

**Files:**
- Create: `src/newsletter_api/ingestion/rss_fetcher.py`
- Create: `src/newsletter_api/ingestion/html_fetcher.py`
- Create: `src/newsletter_api/ingestion/pipeline.py`
- Create: `tests/unit/test_ingestion_pipeline.py`

**Step 1: Write the failing test**

```python
from newsletter_api.ingestion.pipeline import normalize_feed_item


def test_normalize_feed_item_strips_tracking_params():
    raw = {"url": "https://example.com/post?a=1&utm_source=x", "title": "t"}
    item = normalize_feed_item(raw)
    assert item.canonical_url == "https://example.com/post?a=1"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_ingestion_pipeline.py -v`  
Expected: FAIL missing pipeline function

**Step 3: Write minimal implementation**

```python
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse


def canonicalize_url(url: str) -> str:
    parsed = urlparse(url)
    q = [(k, v) for k, v in parse_qsl(parsed.query) if not k.startswith("utm_")]
    return urlunparse(parsed._replace(query=urlencode(q)))
```

Then add RSS fetch first, fallback to HTML fetch for non-RSS sources.

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_ingestion_pipeline.py -v`  
Expected: PASS

**Step 5: Commit**

```bash
git add src/newsletter_api/ingestion/rss_fetcher.py src/newsletter_api/ingestion/html_fetcher.py src/newsletter_api/ingestion/pipeline.py tests/unit/test_ingestion_pipeline.py
git commit -m "feat: implement rss-first ingestion with html fallback"
```

### Task 7: Add Dedup Engine (Canonical + Similarity 0.86)

**Files:**
- Create: `src/newsletter_api/dedup/service.py`
- Create: `tests/unit/test_dedup_service.py`

**Step 1: Write the failing test**

```python
from newsletter_api.dedup.service import should_merge


def test_should_merge_when_similarity_above_threshold():
    assert should_merge("A new GPT release", "New GPT release details", 0.86) is True
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_dedup_service.py -v`  
Expected: FAIL missing `should_merge`

**Step 3: Write minimal implementation**

```python
def should_merge(title_a: str, title_b: str, threshold: float = 0.86) -> bool:
    score = simple_similarity(title_a, title_b)
    return score >= threshold
```

Add canonical URL immediate merge and entity-alignment gate in the service.

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_dedup_service.py -v`  
Expected: PASS

**Step 5: Commit**

```bash
git add src/newsletter_api/dedup/service.py tests/unit/test_dedup_service.py
git commit -m "feat: add mixed dedup strategy with threshold 0.86"
```

### Task 8: Implement Ranking and Slot Allocation

**Files:**
- Create: `src/newsletter_api/ranking/scorer.py`
- Create: `src/newsletter_api/ranking/allocator.py`
- Modify: `ranking.md`
- Create: `tests/unit/test_ranking_allocator.py`

**Step 1: Write the failing test**

```python
from newsletter_api.ranking.allocator import allocate_slots


def test_allocate_slots_has_2_hot_and_6_bottom():
    selected = allocate_slots(sample_candidates())
    assert len(selected.hot) == 2
    assert len(selected.bottom) == 6
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_ranking_allocator.py -v`  
Expected: FAIL missing allocator

**Step 3: Write minimal implementation**

```python
def score(recency, authority, impact, commercial_penalty):
    return (
        0.20 * recency
        + 0.40 * authority
        + 0.30 * impact
        - 0.10 * commercial_penalty
    )
```

Implement:
- dual window ratio 6:4 (0~24h / 24~96h),
- top 2 from different categories,
- bottom 6 with at least 4 categories,
- minimum 3-item fallback behavior.

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_ranking_allocator.py -v`  
Expected: PASS

**Step 5: Commit**

```bash
git add src/newsletter_api/ranking/scorer.py src/newsletter_api/ranking/allocator.py ranking.md tests/unit/test_ranking_allocator.py
git commit -m "feat: implement ranking formula and slot allocation rules"
```

### Task 9: Implement Summarization + Claim Verification

**Files:**
- Create: `src/newsletter_api/summarization/client.py`
- Create: `src/newsletter_api/summarization/verify.py`
- Create: `tests/unit/test_summary_verifier.py`

**Step 1: Write the failing test**

```python
from newsletter_api.summarization.verify import filter_unverified_claims


def test_filter_unverified_claims_removes_mismatch_sentence():
    summary = ["A", "B"]
    verified = {"A": True, "B": False}
    assert filter_unverified_claims(summary, verified) == ["A"]
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_summary_verifier.py -v`  
Expected: FAIL missing verifier

**Step 3: Write minimal implementation**

```python
def filter_unverified_claims(lines: list[str], verification: dict[str, bool]) -> list[str]:
    return [line for line in lines if verification.get(line, False)]
```

Also implement one-model summarization client with strict timeout and failure return.

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_summary_verifier.py -v`  
Expected: PASS

**Step 5: Commit**

```bash
git add src/newsletter_api/summarization/client.py src/newsletter_api/summarization/verify.py tests/unit/test_summary_verifier.py
git commit -m "feat: add summarization client and claim-level verifier"
```

### Task 10: Compose Multipart Campaign (HTML + Text)

**Files:**
- Create: `src/newsletter_api/campaign/composer.py`
- Create: `templates/newsletter.html.j2`
- Create: `templates/newsletter.txt.j2`
- Create: `tests/unit/test_campaign_composer.py`

**Step 1: Write the failing test**

```python
from newsletter_api.campaign.composer import compose_campaign


def test_compose_campaign_returns_html_and_text():
    result = compose_campaign(sample_issue_set())
    assert "<html" in result.html.lower()
    assert "Hot Issue" in result.text
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_campaign_composer.py -v`  
Expected: FAIL because composer/templates are missing

**Step 3: Write minimal implementation**

```python
from jinja2 import Environment, FileSystemLoader

env = Environment(loader=FileSystemLoader("templates"))


def compose_campaign(context):
    html = env.get_template("newsletter.html.j2").render(**context)
    text = env.get_template("newsletter.txt.j2").render(**context)
    return type("CampaignBody", (), {"html": html, "text": text})
```

Ensure template sections include:
- badge line,
- hot issue 2,
- bottom 6,
- satisfaction link,
- unsubscribe link.

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_campaign_composer.py -v`  
Expected: PASS

**Step 5: Commit**

```bash
git add src/newsletter_api/campaign/composer.py templates/newsletter.html.j2 templates/newsletter.txt.j2 tests/unit/test_campaign_composer.py
git commit -m "feat: add multipart campaign composer and templates"
```

### Task 11: Implement Delivery, Redirect Tracking, and Suppression

**Files:**
- Create: `src/newsletter_api/delivery/resend_client.py`
- Create: `src/newsletter_api/delivery/redirect.py`
- Create: `src/newsletter_api/delivery/suppression.py`
- Modify: `src/newsletter_api/main.py`
- Create: `tests/api/test_redirect_and_suppression.py`

**Step 1: Write the failing test**

```python
from fastapi.testclient import TestClient
from newsletter_api.main import app


def test_redirect_endpoint_returns_302():
    client = TestClient(app)
    response = client.get("/r/abc123", follow_redirects=False)
    assert response.status_code == 302
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/api/test_redirect_and_suppression.py -v`  
Expected: FAIL missing redirect route

**Step 3: Write minimal implementation**

```python
@router.get("/r/{token}")
def redirect(token: str):
    url = resolve_redirect_token(token)
    return RedirectResponse(url=url, status_code=302)
```

Add suppression service rules:
- hard bounce => immediate suppress
- soft bounce count >= 3 => suppress

**Step 4: Run test to verify it passes**

Run: `pytest tests/api/test_redirect_and_suppression.py -v`  
Expected: PASS

**Step 5: Commit**

```bash
git add src/newsletter_api/delivery/resend_client.py src/newsletter_api/delivery/redirect.py src/newsletter_api/delivery/suppression.py src/newsletter_api/main.py tests/api/test_redirect_and_suppression.py
git commit -m "feat: add resend delivery, redirect tracking, and suppression rules"
```

### Task 12: Build Celery Workflow and Deterministic 09:00 Scheduler

**Files:**
- Create: `src/newsletter_api/worker/celery_app.py`
- Create: `src/newsletter_api/worker/tasks.py`
- Create: `src/newsletter_api/worker/schedule.py`
- Create: `tests/unit/test_scheduler_rules.py`

**Step 1: Write the failing test**

```python
from newsletter_api.worker.schedule import should_send_now


def test_should_send_now_for_weekday_0900_kst():
    assert should_send_now("2026-02-24T09:00:00+09:00") is True
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_scheduler_rules.py -v`  
Expected: FAIL missing scheduler rule

**Step 3: Write minimal implementation**

```python
from datetime import datetime


def should_send_now(iso_dt: str) -> bool:
    dt = datetime.fromisoformat(iso_dt)
    return dt.weekday() < 5 and dt.hour == 9 and dt.minute == 0
```

Add Celery chain:
- ingest -> dedup -> rank -> summarize -> verify -> link check -> compose -> send.
- strict cutoff policy: no delay, exclude incomplete items.

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_scheduler_rules.py -v`  
Expected: PASS

**Step 5: Commit**

```bash
git add src/newsletter_api/worker/celery_app.py src/newsletter_api/worker/tasks.py src/newsletter_api/worker/schedule.py tests/unit/test_scheduler_rules.py
git commit -m "feat: add celery orchestration and strict 09:00 scheduler"
```

### Task 13: Enforce Idempotent Delivery Constraint

**Files:**
- Modify: `src/newsletter_api/models.py`
- Create: `alembic/versions/20260224_0002_delivery_idempotency.py`
- Create: `tests/unit/test_delivery_idempotency.py`

**Step 1: Write the failing test**

```python
from newsletter_api.models import Delivery


def test_delivery_has_campaign_subscriber_unique_constraint():
    names = {c.name for c in Delivery.__table__.constraints if getattr(c, "name", None)}
    assert "uq_delivery_campaign_subscriber" in names
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_delivery_idempotency.py -v`  
Expected: FAIL unique constraint missing

**Step 3: Write minimal implementation**

```python
__table_args__ = (
    UniqueConstraint("campaign_id", "subscriber_id", name="uq_delivery_campaign_subscriber"),
)
```

Create migration that adds matching unique index/constraint.

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_delivery_idempotency.py -v`  
Expected: PASS

**Step 5: Commit**

```bash
git add src/newsletter_api/models.py alembic/versions/20260224_0002_delivery_idempotency.py tests/unit/test_delivery_idempotency.py
git commit -m "feat: enforce idempotent campaign delivery constraint"
```

### Task 14: Add End-to-End Pipeline Test and Compose Runtime

**Files:**
- Create: `docker-compose.yml`
- Create: `.env.example`
- Create: `tests/e2e/test_daily_campaign_pipeline.py`
- Create: `scripts/run_daily_pipeline.py`

**Step 1: Write the failing test**

```python
def test_daily_campaign_pipeline_generates_campaign_and_deliveries():
    result = run_pipeline_for("2026-02-24")
    assert result.campaign_created is True
    assert result.delivery_count > 0
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/e2e/test_daily_campaign_pipeline.py -v`  
Expected: FAIL because pipeline runner is missing

**Step 3: Write minimal implementation**

```python
def run_pipeline_for(day: str):
    # invoke Celery tasks synchronously in test mode
    # return structured result for assertions
    ...
```

Also create Docker Compose services: `api`, `worker`, `beat`, `postgres`, `redis`.

**Step 4: Run test to verify it passes**

Run: `pytest tests/e2e/test_daily_campaign_pipeline.py -v`  
Expected: PASS

**Step 5: Commit**

```bash
git add docker-compose.yml .env.example tests/e2e/test_daily_campaign_pipeline.py scripts/run_daily_pipeline.py
git commit -m "test: add e2e daily campaign pipeline coverage"
```

### Task 15: Verification Gate Before Merge

**Files:**
- Modify: `README.md`
- Create: `docs/runbooks/daily-ops.md`

**Step 1: Write failing doc checklist test (optional)**

```bash
test -f docs/runbooks/daily-ops.md
```

**Step 2: Run full verification**

Run: `pytest -v`  
Expected: PASS all tests

Run: `alembic upgrade head`  
Expected: migrations applied without error

Run: `docker compose up -d --build && docker compose ps`  
Expected: all services healthy

**Step 3: Update docs with exact operator steps**

Include:
- 09:00 KST campaign run behavior,
- cutoff semantics,
- suppression policy,
- queue waitlist behavior,
- failure troubleshooting.

**Step 4: Re-run verification**

Run: `pytest -v && docker compose down`  
Expected: PASS then clean shutdown

**Step 5: Commit**

```bash
git add README.md docs/runbooks/daily-ops.md
git commit -m "docs: add ops runbook and verification checklist"
```

## Definition of Done

- All task-level tests pass.
- E2E campaign test passes.
- Delivery idempotency is enforced in DB.
- Scheduler emits weekday-only 09:00 KST campaigns.
- Final behavior matches `FINAL_SPEC.md`, `sources.yaml`, `ranking.md`.
