# Runtime Proof Gap Register - 2026-05-18

## Current classification

`CLOUD_READY_PENDING_PROVIDER`

## Purpose

Track every proof gap that cannot be closed by GitHub-only automation.

## Gap register

| Gap | Current state | Required proof | Closure condition |
|---|---|---|---|
| 012A static validation evidence | passed from direct PowerShell output | none for static validation | closed for current checkpoint |
| 012B targeted pytest evidence | passed from direct PowerShell output | none for targeted pytest | closed for targeted pytest only |
| 014 local API smoke evidence | passed 6/6 from local API | none for local smoke | closed for local checkpoint |
| 014 local performance evidence | passed from local p95 measurement | none for local perf | closed for local checkpoint |
| 015 deep audit/perf evidence | partial passed | 016 clean pytest rerun for pytest blocker | superseded by 016 for clean full pytest blocker |
| 016 clean full pytest evidence | passed from GitHub Actions output | none for clean full pytest | closed for current checkpoint |
| Hosted smoke classification hardening | completed in `scripts/cloud_smoke_check.py` | script must not classify endpoint-only success as runtime ready | closed for current checkpoint |
| Public backend runtime | not verified | public HTTPS API URL | root and smoke endpoints respond |
| Cloud DB/PostGIS runtime | not verified | provider DB config outside repo | backend confirms DB-backed endpoints work |
| Hosted smoke 6/6 | not verified | cloud smoke output | hosted smoke passes all required endpoints |
| Public frontend runtime | not verified | public frontend URL | browser loads UI and calls hosted API |
| Hosted performance | not verified | p95 metrics from public API | hosted p95 gates recorded |

## Local evidence note

012A static validation passed.

012B targeted pytest passed.

014 local API smoke passed 6/6 and local performance passed.

016 clean full pytest passed with `pytest_collection_guard_status=passed`, `full_pytest_status=passed`, and `pytest_exit_code=0`.

These local and GitHub Actions results do not prove public cloud runtime readiness.

## Hardening note

`cloud_smoke_check.py` now keeps `CLOUD_READY_PENDING_PROVIDER` unless public backend HTTPS, cloud DB/PostGIS confirmation, hosted smoke 6/6, and public frontend URL are all verified. Endpoint-only success is no longer enough to claim `CLOUD_RUNTIME_READY`.

## GitHub-only status

GitHub-only work can keep this register updated, but it cannot close public runtime proof gaps without a hosted execution surface.

## Allowed closure evidence

- Local runner-published reports.
- Direct PowerShell reports committed to GitHub.
- Hosted CI reports that do not require secrets.
- Hosted smoke output against a public backend URL.
- Provider-side confirmation entered as a secret-safe report.

## Safety

- No secret values in evidence.
- No `.env` or `.env.local` commits.
- No DB write, DDL, migration apply, or production deploy from this checkpoint flow.

## Next action

`WAIT_FOR_USER_PROVIDER_DECISION`