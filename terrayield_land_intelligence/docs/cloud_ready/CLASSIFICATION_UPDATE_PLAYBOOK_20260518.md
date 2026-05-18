# Classification Update Playbook - 2026-05-18

## Current classification

`CLOUD_READY_PENDING_PROVIDER`

## Purpose

Define exact rules for changing classification after new local, CI, or hosted evidence appears.

## Do not change classification for

- GitHub-only documentation updates.
- Manifest updates without runtime evidence.
- Local-only `127.0.0.1` smoke.
- Provider decision without hosted smoke.
- Public frontend URL without backend/API smoke.

## Local evidence effect

If 012A/012B reports appear and pass:

- Update local evidence fields.
- Keep project classification as `CLOUD_READY_PENDING_PROVIDER`.
- Record local readiness improvement only.

## Hosted backend evidence effect

If public backend URL exists but smoke fails:

- classification=`BLOCKED`
- next_single_action=`FIX_HOSTED_SMOKE_FAILURE`

If public backend URL exists and smoke passes but cloud DB is not verified:

- classification=`CLOUD_READY_PENDING_PROVIDER`
- next_single_action=`VERIFY_CLOUD_DB_PROVIDER`

If public backend URL exists, cloud DB is verified, and hosted smoke passes:

- classification=`CLOUD_RUNTIME_READY`
- next_single_action=`VERIFY_FRONTEND_PUBLIC_RUNTIME`

## Frontend evidence effect

If backend is ready and frontend public URL works:

- keep `CLOUD_RUNTIME_READY`, or
- use `FREE_TIER_BEST_EFFORT_READY` only when free-tier constraints are accepted.

## Files to update on classification change

- `CURRENT_STATUS_20260517.md`
- `CURRENT_STATUS_MACHINE_20260518.json`
- `FINAL_MANIFEST_20260517.json`
- `INDEX_TR.md`
- `RUNTIME_PROOF_GAP_REGISTER_20260518.md`
- `NEXT_OPERATOR_HANDOFF_20260518.md`

## Required safety fields in every update

- secret_values_printed=false
- db_write=none
- ddl=none
- migration_apply=none
- prod_deploy=none

## Final reminder

No classification upgrade is allowed without evidence. Local smoke is not public cloud proof.
