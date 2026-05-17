# TerraYield AI Cloud Readiness - Parallel Execution Board

## Current classification

`CLOUD_READY_PENDING_PROVIDER`

## Open execution tracks

| Track | GitHub issue | Purpose | Blocking dependency |
|---|---:|---|---|
| Provider master blocker | #8 | Overall provider setup gate | Public URL + cloud DB |
| Backend public API | #9 | Hosted API runtime | Provider web service |
| Cloud PostGIS/database | #10 | Managed database setup | Provider DB settings |
| Frontend public hosting | #11 | Browser access from any device | Backend public URL |
| Performance/cold start | #12 | Hosted p95/cold-start check | Public runtime |
| Local path/data migration | #13 | Remove local-only runtime dependencies | Cloud data strategy |

## Parallel work policy

These tracks can progress in parallel. Do not wait for Codex unless a track needs external provider state or fresh local runtime evidence.

## Completion order

1. Configure cloud DB provider outside the repository.
2. Deploy backend with `Dockerfile.cloud`.
3. Set public API URL outside the repository.
4. Run `scripts/cloud_smoke_check.py` against hosted API.
5. Deploy frontend and point it to hosted backend.
6. Run hosted performance gates.
7. Verify local path/data dependency migration.
8. Update classification.

## Classification rules

- Keep `CLOUD_READY_PENDING_PROVIDER` until public hosted API URL and cloud DB are verified.
- Use `CLOUD_RUNTIME_READY` only after hosted smoke passes.
- Use `FREE_TIER_BEST_EFFORT_READY` only after hosted smoke passes and free-tier constraints are documented.
- Use `BLOCKED` for any failed hosted smoke or missing provider dependency.

## Existing repo-side completion

- Cloud scaffold exists.
- Static validator exists.
- Handoff control files exist.
- GitHub Actions static workflow exists.
- Provider blocker issue exists.
- Parallel execution issues exist.

## Safety

- No real secrets in repository.
- No `.env` or `.env.local` commits.
- No production deploy or migrations without explicit user approval.
- No false claim of public cloud readiness from local `127.0.0.1` smoke.
