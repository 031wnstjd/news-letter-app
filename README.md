# News Letter App

AI/Dev 데일리 뉴스레터 MVP 저장소입니다.

## Documents
- Final spec: `FINAL_SPEC.md`
- Source policy: `sources.yaml`
- Ranking model: `ranking.md`
- Implementation plan: `docs/plans/2026-02-24-ai-dev-daily-newsletter-mvp.md`
- AI+Frontend design: `docs/plans/2026-02-24-ai-summarization-frontend-design.md`
- AI+Frontend implementation plan: `docs/plans/2026-02-24-ai-summarization-frontend-implementation.md`
- Ops runbook: `docs/runbooks/daily-ops.md`

## Local Development
```bash
pip install -e .[dev]
pytest -q
```

## Real AI Summarization Setup
Set environment variables before running API:

```bash
export OPENAI_API_KEY="your_openai_key"
export OPENAI_MODEL="gpt-4o-mini"   # optional
export OPENAI_BASE_URL="https://api.openai.com/v1"  # optional
```

If `OPENAI_API_KEY` is missing:
- Newsletter preview still works with deterministic fallback summaries.
- Manual summarize API returns an explicit key-missing error.

## API
- `GET /health`
- `POST /v1/subscribers`
- `POST /v1/subscribers/verify/{token}`
- `GET /r/{token}`
- `GET /v1/newsletter/preview`
- `POST /v1/summaries/generate`

## Frontend
- `GET /` : interactive UI for:
  - live RSS-based newsletter preview generation
  - manual AI summary generation for custom article text

## Infra
```bash
docker compose up -d --build
docker compose ps
```
