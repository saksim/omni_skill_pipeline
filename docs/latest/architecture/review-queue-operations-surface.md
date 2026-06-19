# Review Queue Operations Surface

> Date: 2026-04-25  
> Task Card: `LC-R-37`  
> Scope: expose review queue operations (`list` / `claim` / `close`) for runtime triage flow

## Verdict

`ReviewQueueRepository` now provides explicit operations for:

- listing review tasks by queue bucket (`pending` / `consumed` / `closed`)
- claiming a specific pending task (or oldest pending task)
- closing a claimed/pending task with closure metadata

API surface in `api_app.py` exposes these contracts under `/v1/review/queue*`.

## Runtime Contract

Repository protocol:

- `list_review_queue(queue_status='pending', limit=100)`
- `claim_review_task(review_task_id=None, consumer='review-consumer')`
- `close_review_task(review_task_id, status='published', closed_by='review-operator', review_notes='')`

Compatibility:

- existing `consume_review_task(...)` is retained as a compatibility alias to `claim_review_task(...)`.

## Storage Contract (File Repository)

Queue buckets under `<draft_dir>/review_queue/`:

- `pending/*.json`
- `consumed/*.json`
- `closed/*.json`

Transition semantics:

1. enqueue -> `pending`
2. claim -> move file to `consumed`, stamp `claimed_by/claimed_at/consumed_at`
3. close -> move file to `closed`, stamp `closed_by/closed_at`, update `status` and optional `review_notes`

## API Contract

- `GET /v1/review/queue`
- `POST /v1/review/queue/claim`
- `POST /v1/review/queue/{review_task_id}/close`

All three endpoints reuse existing API key and rate-limit middleware.

## Test Landing

- `tests/test_review_queue_repository.py`
- `tests/test_review_queue_integration.py`
- `tests/test_api_review_queue.py`
- `scripts/tp_tests.py` -> `TP-E9-03`
