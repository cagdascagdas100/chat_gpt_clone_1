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
| 012B local API smoke evidence | not run | local API smoke output | API smoke endpoints pass |
| 012B local performance evidence | not run | local p95 metrics | local p95 gates recorded |
| Public backend runtime | not verified | public HTTPS API URL | root and smoke endpoints respond |
| Cloud DB/PostGIS runtime | not verified | provider DB config outside repo | backend confirms DB-backed endpoints work |
| Hosted smoke 6/6 | not verified | cloud smoke output | hosted smoke passes all required endpoints |
| Public frontend runtime | not verified | public frontend URL | browser loads UI and calls hosted API |
| Hosted performance | not verified | p95 metrics from public API | hosted p95 gates recorded |

## 012A / 012B note

012A static validation has passed from direct PowerShell output.

012B targeted pytest has passed from direct PowerShell output. API smoke and performance checks were not run in that same report, so those remain open.

## GitHub-only status

GitHub-only work can keep this register updated, but it cannot close public runtime proof gaps without a local or hosted execution surface.

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
