# Watchdog Runner Usage - 2026-05-18

## Purpose

This document explains how the safe watchdog runner should be used after GitHub-only preparation reaches its limit.

## Script

`docs/chatgpt_handoff/local_runner_queue/AAYS_LOCAL_RUNNER_WATCHDOG_SAFE.ps1`

## Current classification

`CLOUD_READY_PENDING_PROVIDER`

## What the watchdog is allowed to do

- Pull the target branch.
- Read tasks from `docs/chatgpt_handoff/local_runner_queue/inbox`.
- Execute allowlisted read/test/smoke/perf tasks.
- Write stdout/stderr logs.
- Move successful tasks to `done`.
- Move failed or rejected tasks to `failed`.
- Publish generated reports back to GitHub.

## Current allowlist

- `012A_STATIC_CLOUD_READY_VALIDATE_AND_PUBLISH.ps1`
- `012B_LOCAL_TEST_SMOKE_PERF_AND_PUBLISH.ps1`

## Safety policy

The watchdog must keep:

- `db_write=none`
- `ddl=none`
- `migration_apply=none`
- `prod_deploy=none`
- `secret_values_printed=false`

## Expected heartbeat

`docs/chatgpt_handoff/local_runner_queue/outputs/WATCHDOG_HEARTBEAT.txt`

Expected heartbeat fields:

- timestamp_utc
- repo
- branch
- status
- task
- safe_mode
- db_write
- ddl
- migration_apply
- prod_deploy
- secret_values_printed

## Expected evidence outputs

From 012A:

- static validation report
- static validation blockers
- static validator output

From 012B:

- targeted pytest output
- local API smoke output
- performance summary
- local test/smoke/perf report
- local test/smoke/perf blockers

## When classification may change

Do not upgrade from `CLOUD_READY_PENDING_PROVIDER` unless fresh evidence proves the required gate.

For cloud readiness, public URL and cloud DB proof are still required.
