# News Letter App

AI/Dev 데일리 뉴스레터 MVP 저장소입니다.

## Documents
- Final spec: `FINAL_SPEC.md`
- Source policy: `sources.yaml`
- Ranking model: `ranking.md`
- Implementation plan: `docs/plans/2026-02-24-ai-dev-daily-newsletter-mvp.md`
- Ops runbook: `docs/runbooks/daily-ops.md`

## Local Development
```bash
pip install -e .[dev]
pytest -q
```

## API
- `GET /health`
- `POST /v1/subscribers`
- `POST /v1/subscribers/verify/{token}`
- `GET /r/{token}`

## Infra
```bash
docker compose up -d --build
docker compose ps
```
