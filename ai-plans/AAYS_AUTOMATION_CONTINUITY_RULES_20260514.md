# AAYS Automation Continuity Rules

Generated: 2026-05-14

## Problem
The remote continuation flow fails when `current-task.json` is not in the runner-compatible task format. The runner does not execute chat text directly. It only reacts to repository state changes that it can poll from the local bridge checkout.

## Required invariant
Every executable task in `ai-tasks/current-task.json` must include:

- `id`: unique task id, never reused
- `title`: readable task title
- `working_directory`: `C:\AAYS_GITHUB_BRIDGE_CLEAN2`
- `timeout_seconds`: bounded timeout
- `script_path`: a script under `ai-task-scripts`
- `continuation_protocol`: true
- `wait_minutes_after_start`: expected wait window

## Forbidden for executable tasks
- Do not use action-only tasks without `script_path`.
- Do not reuse an id already present in `.last-task-id`.
- Do not leave `final_lock: true` when a new task must be executed.
- Do not mark `no_new_tasks: true` when continuation is expected.

## Local runner requirement
The user startup launcher must exist:

`AAYS_V6_SAFE_SYNC_RUNNER.cmd`

in the user Startup folder. It should launch the V6 safe sync runner from `C:\AAYS_GITHUB_BRIDGE_CLEAN2`.

## Verified final acceptance
The final local acceptance run reported:

- accepted: true
- readiness_score: 100
- user_startup_launcher: true
- remaining gaps: none

## Operating rule
When the user says `devam et`, create or update a new unique `current-task.json` that follows the invariant above, then check heartbeat and result files after the wait window.
