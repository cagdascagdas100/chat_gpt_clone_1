# Watchdog Readiness Closure - 2026-05-18

## Current classification

`CLOUD_READY_PENDING_PROVIDER`

## Current next action

`WAIT_FOR_USER_PROVIDER_DECISION`

## Watchdog layer status

Prepared but not enabled.

## Prepared files

- `docs/chatgpt_handoff/local_runner_queue/AAYS_LOCAL_RUNNER_WATCHDOG_SAFE.ps1`
- `docs/cloud_ready/SAFE_RUNNER_TASK_PROTOCOL_20260518.md`
- `docs/cloud_ready/PERSISTENT_RUNNER_WATCHDOG_DESIGN_20260518.md`
- `docs/cloud_ready/WATCHDOG_RUNNER_USAGE_TR_20260518.md`
- `docs/cloud_ready/WATCHDOG_EVIDENCE_TEMPLATE_20260518.txt`
- `scripts/validate_watchdog_readiness.py`

## What this enables

If manually started once, the watchdog can pull safe queued tasks, run allowlisted checks, publish reports, and reduce repeated user intervention.

## Why it is not enabled automatically

Starting a persistent local runner requires execution on the user's local PC. GitHub-only automation can prepare the script but cannot start a local Windows PowerShell process by itself.

## What remains blocked without enablement

- fresh local pytest evidence
- fresh local API smoke evidence
- fresh p95 performance evidence
- 012A report publication
- 012B report publication

## Provider-side blockers still remain

- public backend HTTPS URL
- cloud DB/PostGIS provider configuration
- hosted smoke 6/6
- public frontend URL

## Safety invariant

- db_write=none
- ddl=none
- migration_apply=none
- prod_deploy=none
- secret_values_printed=false
