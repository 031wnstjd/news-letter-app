# AI Summarization + Frontend Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement real OpenAI-backed newsletter summarization and a working frontend UI that generates live preview content and manual summaries.

**Architecture:** Extend existing FastAPI service with a concrete AI summarizer, RSS-driven preview pipeline, and frontend routes/templates. Keep the current package layout, add targeted modules, and validate behavior through deterministic unit/API tests with mocked network.

**Tech Stack:** FastAPI, httpx, feedparser, Jinja2, vanilla JS, pytest.

---

### Task 1: Add Failing Tests for AI Summarizer

**Files:**
- Create: `tests/unit/test_ai_summarizer.py`
- Modify: `pyproject.toml`

**Step 1: Write the failing test**

```python
def test_ai_summarizer_parses_model_json_response():
    ...
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_ai_summarizer.py -q`  
Expected: FAIL (module/function missing)

**Step 3: Write minimal implementation**

Add OpenAI client logic in `src/newsletter_api/summarization/client.py`.

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_ai_summarizer.py -q`  
Expected: PASS

**Step 5: Commit**

```bash
git add tests/unit/test_ai_summarizer.py src/newsletter_api/summarization/client.py pyproject.toml
git commit -m "feat: add openai-backed summarizer with unit tests"
```

### Task 2: Add RSS Fetcher Tests and Real RSS Parsing

**Files:**
- Modify: `src/newsletter_api/ingestion/rss_fetcher.py`
- Create: `tests/unit/test_rss_fetcher.py`
- Modify: `sources.yaml`

**Step 1: Write the failing test**

```python
def test_fetch_rss_items_normalizes_entry_fields():
    ...
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_rss_fetcher.py -q`  
Expected: FAIL

**Step 3: Write minimal implementation**

Use `feedparser.parse` and normalize into expected item dictionaries.

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_rss_fetcher.py -q`  
Expected: PASS

**Step 5: Commit**

```bash
git add src/newsletter_api/ingestion/rss_fetcher.py tests/unit/test_rss_fetcher.py sources.yaml
git commit -m "feat: implement rss ingestion with normalized items"
```

### Task 3: Add Preview Pipeline + Endpoint Tests

**Files:**
- Create: `src/newsletter_api/newsletter/__init__.py`
- Create: `src/newsletter_api/newsletter/pipeline.py`
- Create: `src/newsletter_api/newsletter/routes.py`
- Modify: `src/newsletter_api/main.py`
- Create: `tests/api/test_newsletter_preview_api.py`

**Step 1: Write the failing test**

```python
def test_newsletter_preview_endpoint_returns_slots():
    ...
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/api/test_newsletter_preview_api.py -q`  
Expected: FAIL

**Step 3: Write minimal implementation**

Create preview pipeline and wire `GET /v1/newsletter/preview`.

**Step 4: Run test to verify it passes**

Run: `pytest tests/api/test_newsletter_preview_api.py -q`  
Expected: PASS

**Step 5: Commit**

```bash
git add src/newsletter_api/newsletter src/newsletter_api/main.py tests/api/test_newsletter_preview_api.py
git commit -m "feat: add newsletter preview pipeline and api route"
```

### Task 4: Add Manual Summarize API

**Files:**
- Create: `src/newsletter_api/summarization/routes.py`
- Modify: `src/newsletter_api/main.py`
- Create: `tests/api/test_summarize_api.py`

**Step 1: Write the failing test**

```python
def test_generate_summary_endpoint_returns_structured_lines():
    ...
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/api/test_summarize_api.py -q`  
Expected: FAIL

**Step 3: Write minimal implementation**

Add `POST /v1/summaries/generate`.

**Step 4: Run test to verify it passes**

Run: `pytest tests/api/test_summarize_api.py -q`  
Expected: PASS

**Step 5: Commit**

```bash
git add src/newsletter_api/summarization/routes.py src/newsletter_api/main.py tests/api/test_summarize_api.py
git commit -m "feat: add manual summary generation api"
```

### Task 5: Implement Frontend UI + Route Tests

**Files:**
- Create: `src/newsletter_api/frontend/__init__.py`
- Create: `src/newsletter_api/frontend/routes.py`
- Create: `templates/web/index.html.j2`
- Create: `static/app.css`
- Create: `static/app.js`
- Modify: `src/newsletter_api/main.py`
- Create: `tests/api/test_frontend_page.py`

**Step 1: Write the failing test**

```python
def test_frontend_root_page_renders():
    ...
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/api/test_frontend_page.py -q`  
Expected: FAIL

**Step 3: Write minimal implementation**

Mount static files and serve a JS-enabled preview/summarize UI.

**Step 4: Run test to verify it passes**

Run: `pytest tests/api/test_frontend_page.py -q`  
Expected: PASS

**Step 5: Commit**

```bash
git add src/newsletter_api/frontend templates/web/index.html.j2 static src/newsletter_api/main.py tests/api/test_frontend_page.py
git commit -m "feat: add interactive frontend for preview and ai summary"
```

### Task 6: Full Verification + Runtime Check

**Files:**
- Modify: `README.md`

**Step 1: Run full tests**

Run: `pytest -q`  
Expected: PASS

**Step 2: Run local service smoke check**

Run: `docker compose up -d --build`  
Run: `curl -s http://localhost:8000/health`  
Run: `curl -s http://localhost:8000/docs >/dev/null`

Expected: healthy response and docs accessible.

**Step 3: Document setup for real AI**

Add OpenAI env instructions in `README.md`.

**Step 4: Final cleanup**

Run: `docker compose down`  
Expected: all containers removed.

**Step 5: Commit**

```bash
git add README.md
git commit -m "docs: add ai summarization and frontend runtime instructions"
```
