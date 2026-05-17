# Persistent Runner Upgrade Package - 2026-05-18

## Purpose

This package defines the next autonomy layer after GitHub-only preparation.

## Current status

`CLOUD_READY_PENDING_PROVIDER`

`WAIT_FOR_USER_PROVIDER_DECISION`

## Why this is needed

GitHub-only automation can prepare files and plans, but cannot produce fresh local runtime evidence. A persistent runner can bridge that gap by polling the GitHub queue and publishing evidence back to the repository.

## Runner duties

A persistent local runner should:

1. Pull `security-accuracy-expansion-20260508`.
2. Read queued tasks from `docs/chatgpt_handoff/local_runner_queue/inbox`.
3. Run only approved read/test/smoke/perf tasks.
4. Move completed tasks to `done` or `failed`.
5. Publish reports to `docs/chatgpt_handoff/cloud_ready_20260517`.
6. Push evidence back to GitHub.

## Must publish

- pytest report
- local API smoke report
- performance summary
- safety summary
- final execution report

## Safety rules

The runner must not run:

- DB writes
- DDL
- migration apply
- production deploy
- secret printing

## Current blocked queued tasks

- `012A_STATIC_CLOUD_READY_VALIDATE_AND_PUBLISH.ps1`
- `012B_LOCAL_TEST_SMOKE_PERF_AND_PUBLISH.ps1`

These were queued, but their reports have not appeared on GitHub.

## Upgrade recommendation

Create a watchdog runner that:

- starts once,
- polls the inbox every few minutes,
- writes heartbeat logs,
- pushes evidence automatically,
- refuses unsafe tasks by default.

## Result if enabled

If this runner is enabled, the user can continue typing only `devam` while the runner publishes fresh local evidence.

## Result if not enabled

The project remains in GitHub-only mode and keeps the correct classification:

`CLOUD_READY_PENDING_PROVIDER`
