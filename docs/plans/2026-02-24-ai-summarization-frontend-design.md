# AI Summarization + Frontend Design

Date: 2026-02-24

## Context
- Existing backend is scaffolded and tested but summarization is stubbed.
- No user-facing frontend exists yet.
- User requested autonomous completion without further intervention.

## Assumptions
- User delegated decision authority for implementation details ("알아서 계획 기반으로").
- `OPENAI_API_KEY` will be provided in runtime environments where real AI summarization is expected.
- If API key is missing, system should still render UI and provide explicit setup guidance.

## Goals
- Replace deterministic placeholder summary with real LLM-backed summarization.
- Provide a production-like frontend where user can:
  - generate live RSS-based newsletter preview,
  - run on-demand article summarization.
- Keep existing API/test architecture and avoid a framework migration.

## Non-Goals
- Full production queue orchestration for all scheduled jobs.
- Rich admin CMS for manual curation.
- Personalization rollout (already deferred by prior spec).

## Architecture
1. AI Summarization Layer
- Add OpenAI Chat Completions client using `httpx`.
- Enforce structured JSON output from model:
  - `tldr` (2 lines),
  - `why_it_matters` (1 line),
  - `practical_apply` (1 line).
- Return `SummaryResult(ok=False)` with explicit error if key is missing or call fails.

2. Ingestion-to-Preview Pipeline
- Implement real RSS parsing via `feedparser`.
- Extend sources with concrete `rss_url` values.
- Build lightweight preview pipeline:
  - collect -> normalize -> dedup(URL canonical) -> score -> allocate slots(2 hot + 6 bottom) -> summarize.
- Keep ranking rules aligned with `ranking.md` defaults.

3. Frontend UI/UX
- FastAPI server-rendered page at `/` plus JS-driven API calls.
- Style direction from `ui-ux-pro-max`:
  - Exaggerated Minimalism,
  - Fira Code / Fira Sans typography,
  - palette:
    - primary `#0369A1`
    - secondary `#0EA5E9`
    - CTA `#F97316`
    - background `#F0F9FF`
    - text `#0C4A6E`
- Features:
  - hero with one-click preview generation,
  - card-based result sections (Hot/More),
  - manual summary form,
  - responsive layout and reduced-motion support.

## API Surface
- `GET /v1/newsletter/preview` -> live newsletter JSON, optional query limits.
- `POST /v1/summaries/generate` -> summarize one item.
- `GET /` -> frontend app page.

## Error Handling
- Missing OpenAI key:
  - API returns actionable error message.
  - Frontend shows setup banner (`OPENAI_API_KEY required`).
- RSS source fetch failures:
  - skip failed source, continue best-effort generation.
- No items collected:
  - return empty preview with badge message.

## Testing Strategy
- Unit:
  - OpenAI client request/response parsing,
  - RSS parsing transformation.
- API:
  - preview endpoint response shape,
  - summarize endpoint success/failure path,
  - frontend page rendering.
- Keep deterministic by mocking network in tests.

## Trade-offs
- Chosen: server-rendered + vanilla JS frontend (fast integration, low complexity).
- Rejected: React/Next migration (high churn for current repository state).
- Chosen: OpenAI direct integration first (fastest path to real AI).
- Rejected: multi-provider abstraction now (can be added later).
