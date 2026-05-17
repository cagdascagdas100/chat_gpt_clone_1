# User Provider Decision Request - 2026-05-17

## Current classification

`CLOUD_READY_PENDING_PROVIDER`

## Required decision before continuing

Choose the hosted stack for TerraYield AI:

1. Backend hosting provider.
2. Cloud Postgres/PostGIS provider.
3. Frontend public hosting provider.
4. Public backend HTTPS URL after deploy.
5. Approval to run hosted smoke against that public URL.

## Current repo-side status

Prepared:

- Cloud scaffold files.
- Static validator.
- Hosted smoke script.
- GitHub Actions workflow file.
- Cloud-ready docs.
- Handoff/control reports.
- Parallel execution board.
- Operator stop condition.
- 012C GitHub-native fallback report.

Not yet verified:

- 012A runner report.
- 012B runner report.
- GitHub Actions workflow run visibility.
- Public hosted HTTPS URL.
- Cloud DB provider configuration.
- Hosted smoke 6/6.

## Allowed next classifications

- Keep `CLOUD_READY_PENDING_PROVIDER` until provider values exist.
- Use `CLOUD_RUNTIME_READY` only after hosted smoke passes.
- Use `FREE_TIER_BEST_EFFORT_READY` only after hosted smoke passes and free-tier limits are accepted.

## Safety

- No real secrets in repo.
- No `.env` or `.env.local` commit.
- No DB write.
- No DDL.
- No migration apply.
- No production deploy without explicit approval.

## Current next action

`WAIT_FOR_USER_PROVIDER_DECISION`
