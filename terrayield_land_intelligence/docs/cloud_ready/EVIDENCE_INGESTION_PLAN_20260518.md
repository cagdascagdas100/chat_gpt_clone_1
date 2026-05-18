# Evidence Ingestion Plan - 2026-05-18

## Current classification

`CLOUD_READY_PENDING_PROVIDER`

## Current operating policy

`AUTONOMOUS_LONG_RUN`

## Purpose

Define how new evidence should be ingested when it appears from local runner, hosted CI, or cloud provider smoke checks.

## Evidence sources

| Source | Expected evidence | Can update classification? |
|---|---|---|
| GitHub-only docs | manifests, plans, templates | no |
| Local watchdog runner | pytest, local smoke, local p95 | local readiness only |
| Hosted CI | static or public-safe checks | partial only |
| Public backend smoke | hosted endpoint checks | yes, if 6/6 passes |
| Cloud DB verification | DB-backed endpoint evidence | yes, with hosted smoke |
| Frontend public smoke | browser/UI public URL evidence | user-facing readiness only |

## Ingestion rules

1. New evidence must be stored under `docs/chatgpt_handoff/cloud_ready_20260517` or `docs/cloud_ready`.
2. Evidence must not include real secrets.
3. Evidence must include a classification recommendation.
4. Evidence must include safety fields.
5. Evidence must not claim public cloud readiness from local `127.0.0.1` checks.

## Classification updates

Keep `CLOUD_READY_PENDING_PROVIDER` if:

- provider URL is missing,
- cloud DB is missing,
- hosted smoke is missing,
- only GitHub-only evidence exists.

Use `CLOUD_RUNTIME_READY` if:

- public backend URL exists,
- cloud DB is configured outside repo,
- hosted smoke passes all required endpoints.

Use `FREE_TIER_BEST_EFFORT_READY` only if:

- `CLOUD_RUNTIME_READY` evidence exists,
- free-tier limits are accepted and documented.

Use `BLOCKED` if:

- hosted smoke fails,
- unsafe action is requested,
- required runtime proof contradicts readiness.

## Files to update after new evidence

- `docs/cloud_ready/CURRENT_STATUS_20260517.md`
- `docs/cloud_ready/CURRENT_STATUS_MACHINE_20260518.json`
- `docs/cloud_ready/FINAL_MANIFEST_20260517.json`
- `docs/cloud_ready/RUNTIME_PROOF_GAP_REGISTER_20260518.md`
- `docs/cloud_ready/INDEX_TR.md`

## Safety invariant

- db_write=none
- ddl=none
- migration_apply=none
- prod_deploy=none
- secret_values_printed=false
