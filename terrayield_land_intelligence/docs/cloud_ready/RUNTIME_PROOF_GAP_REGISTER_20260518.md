# Runtime Proof Gap Register - 2026-05-18

## Current classification

`CLOUD_READY_PENDING_PROVIDER`

## Purpose

Track every proof gap that cannot be closed by GitHub-only automation.

## Gap register

| Gap | Current state | Required proof | Closure condition |
|---|---|---|---|
| 012A static runner evidence | status-placeholder visible, success not verified | actual 012A runner output | `actual_task_output_found=true` and validation passes |
| 012B local test/smoke/perf evidence | status-placeholder visible, success not verified | actual 012B runner output | pytest, smoke, and perf evidence pass |
| Public backend runtime | not verified | public HTTPS API URL | root and smoke endpoints respond |
| Cloud DB/PostGIS runtime | not verified | provider DB config outside repo | backend confirms DB-backed endpoints work |
| Hosted smoke 6/6 | not verified | cloud smoke output | hosted smoke passes all required endpoints |
| Public frontend runtime | not verified | public frontend URL | browser loads UI and calls hosted API |
| Hosted performance | not verified | p95 metrics from public API | hosted p95 gates recorded |

## 012A / 012B note

The current 012A and 012B files are status placeholders created during the Codex-control pass. They keep blockers visible but do not prove successful local runner execution.

## GitHub-only status

GitHub-only work can keep this register updated, but it cannot close the runtime proof gaps without an execution surface.

## Allowed closure evidence

- Local runner-published reports.
- Hosted CI reports that do not require secrets.
- Hosted smoke output against a public backend URL.
- Provider-side confirmation entered as a secret-safe report.

## Safety

- No secret values in evidence.
- No `.env` or `.env.local` commits.
- No DB write, DDL, migration apply, or production deploy from this checkpoint flow.

## Next action

`WAIT_FOR_USER_PROVIDER_DECISION`
