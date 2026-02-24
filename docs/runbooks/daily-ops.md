# Daily Ops Runbook

## Schedule
- Weekdays only
- Campaign cutoff and send: 09:00 KST
- Strict schedule: incomplete items are excluded, no delay

## Daily Execution
1. Confirm ingestion and ranking jobs succeeded.
2. Verify campaign candidate count and badge message.
3. Verify link check completed.
4. Trigger delivery queue if automatic schedule failed.

## Suppression Policy
- Hard bounce: suppress immediately.
- Soft bounce: suppress after 3 cumulative events.

## Waitlist Policy
- When provider limit is reached, existing subscribers are prioritized.
- New subscribers are queued by verification completion timestamp (FIFO).
- Queue status email should be sent immediately.

## Failure Handling
- Summarization or verification failure: exclude affected items.
- Delivery API failure: keep failed deliveries queued for retry.
- Link validation failure: swap to fallback candidate if available.

## Verification Commands
- `pytest -q`
- `alembic upgrade head`
- `docker compose up -d --build`
- `docker compose ps`
