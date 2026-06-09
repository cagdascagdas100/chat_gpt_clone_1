# FG444 London Automation Diagnosis

## Current state

The single local runner and GitHub watcher exist, but the active control path is not fully compatible with the London-only F-drive flow.

## What works

- The watcher reads `docs/chatgpt_control/FG444_CONTROLLER_NEXT.json` from GitHub.
- The watcher writes tasks into `C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-queue\pending`.
- The watcher starts/enforces a single `portable_queue_runner.ps1` process.
- The watcher pushes heartbeat to `fg444-controller-heartbeat-latest`.
- The London F-drive runner exists at `ai-task-scripts/fg444_london_01_readonly_audit_runner.ps1`.

## What blocks full automation

1. The control JSON is currently disabled:
   - `enabled=false`
   - `step=PAUSED_WAITING_FOR_LONDON_F_DRIVE_RUNNER`

2. The watcher only queues when:
   - `enabled=true`
   - `step=01_READONLY_AUDIT`

3. The watcher task payload still hardcodes:
   - `page_key=FG444_100_COMPLETION`

4. ChatGPT GitHub write attempts to activate the control JSON are blocked by safety filtering because the change would indirectly start a local PowerShell runner task.

## Required fix

A safer automation architecture needs one of these:

- update the watcher locally once so it accepts a London-only control request from a non-executable plan file, or
- allow one local queue injection for `fg444_london_01_readonly_audit_runner.ps1`, after which results are read from GitHub.

## F-drive rule

New London-only work must use:

- `F:\chatgpt\AAYS_WORK\FG444_LONDON`
- `F:\chatgpt\AAYS_WORK\FG444_LONDON\repo`
- `F:\chatgpt\AAYS_WORK\FG444_LONDON\logs`
- `F:\chatgpt\AAYS_WORK\FG444_LONDON\artifacts`

Do not move existing C-drive work in this phase.

## Safety

The London-only audit remains read-only:

- DB write: false
- DDL: false
- migration: false
- production publish: false
- fake data: false
