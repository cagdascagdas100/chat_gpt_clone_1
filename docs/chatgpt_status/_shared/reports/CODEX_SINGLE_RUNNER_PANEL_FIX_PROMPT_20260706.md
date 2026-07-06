# CODEX TASK: AAYS single runner + panel + new page pickup fix

Repo root on the user's PC:

`C:\Users\cagda\Documents\GitHub\AAYS`

Branch:

`main`

## Goal

Make one clickable runner command that starts exactly one shared/canonical runner and one panel window. When the user opens this command after a PC reboot, the same runner must continue queued work from GitHub/main. When a new ChatGPT page is opened, its page_key and queue files must be usable by the same runner without creating a second runner.

Do not create parallel runners. Do not write fake completed/final_ready/%100. Do not write outside allowed_paths. Do not do DB write, migration, DDL, or production deploy.

## Current problem evidence

1. The active aays1 queue was previously skipped by the shared runner because of INVALID_QUEUE_CONTRACT. The latest fixed queue now has page_key, target_branch, script_path, allowed_paths, and all no_* safety flags. Recheck this file locally:

`docs/chatgpt_status/aays1/queue/0000_115_security_batch_join_backoff_force_pickup.task.json`

2. The latest shared status is stale and from the old F repo root:

`docs/chatgpt_status/_shared/status/MULTI_PAGE_latest_status.json`

It showed queue_started=false, runner_output_uploaded=false, and skipped aays1 queues as INVALID_QUEUE_CONTRACT.

3. The latest shared heartbeat is also stale and points to the old F repo root:

`docs/chatgpt_status/_shared/heartbeat/MULTI_PAGE_heartbeat_latest.json`

4. The expected aays1 long batch output is still missing:

`docs/chatgpt_status/security_public_safety/runner_outputs/115_security_batch_join_backoff.json`

## Required files to create or fix

Create a one-click command in repo root:

`START_AAYS_SINGLE_RUNNER_AND_PANEL.cmd`

It must call:

`docs/chatgpt_status/_shared/automation/START_AAYS_SINGLE_RUNNER_AND_PANEL.ps1`

Create/fix this PowerShell launcher:

`docs/chatgpt_status/_shared/automation/START_AAYS_SINGLE_RUNNER_AND_PANEL.ps1`

The launcher must:

- Resolve repo root as `C:\Users\cagda\Documents\GitHub\AAYS` by default.
- Run `git fetch`, `git checkout main`, `git pull --ff-only origin main`.
- Run queue normalizer if present.
- Run panel index builder if present.
- Start exactly one shared runner using the canonical entry:
  `docs/chatgpt_status/_shared/automation/RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER.ps1`
- Start one panel window.
- Write local startup status to:
  `docs/chatgpt_status/_shared/status/local_runner_panel_start_latest.json`
- If the runner cannot start, write blocked evidence, not completed evidence.

## Runner root problem to fix

Check this file:

`docs/chatgpt_status/_shared/automation/RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_V4_20260706.ps1`

If it blocks non-F repo roots, remove the hardcoded F-root gate and replace it with a real repo validation:

- RepoRoot must exist.
- RepoRoot must contain `.git`.
- RepoRoot must contain `docs/chatgpt_status/_shared/automation/RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER.ps1`.

The runner must work from:

`C:\Users\cagda\Documents\GitHub\AAYS`

## Single runner lock

The runner must use one lock only:

`docs/chatgpt_status/_shared/runner_lock/MULTI_PAGE.lock`

If the lock is fresh, panel must show `RUNNER_ALREADY_ACTIVE` and must not start another runner.

If the lock is stale, runner may clean it and continue.

## Panel requirements

Create or fix panel script:

`docs/chatgpt_status/_shared/automation/START_AAYS_RUNNER_PANEL.ps1`

The panel may be a PowerShell GUI, browser page, or console dashboard. It must open automatically from the one-click command.

Panel data source:

`docs/chatgpt_status/_shared/status/page_panel_index.json`

If missing, generate it by running:

`docs/chatgpt_status/_shared/automation/BUILD_AAYS_PAGE_PANEL_INDEX.ps1`

The panel must show five menu slots. The menu names will be provided later from the user's screenshot. Until then use placeholders:

1. MENU_1_FROM_SCREENSHOT
2. MENU_2_FROM_SCREENSHOT
3. MENU_3_FROM_SCREENSHOT
4. MENU_4_FROM_SCREENSHOT
5. MENU_5_FROM_SCREENSHOT

Each menu/page row must show:

- page_key
- queue status
- runner active / problem
- heartbeat present or missing
- completed present or missing
- final_ready
- completion percent
- remaining percent
- blocker summary

If all required runner checks are healthy, show `Runner Aktif`.

If not healthy, show the exact blocker, for example:

- stale heartbeat
- missing output
- invalid queue contract
- GitHub auth failed
- push failed
- script missing
- allowed_paths violation
- repo root mismatch

## New ChatGPT page pickup requirement

Make this template ready and canonical:

`docs/chatgpt_status/_shared/templates/NEW_CHATGPT_PAGE_QUEUE_TEMPLATE_20260706.json`

The template must include:

- task_id
- page_key
- status=pending
- target_branch=main
- script_path
- expected_output
- allowed_paths
- no_fake_final_ready=true
- no_db_write=true
- no_migration=true
- no_production_deploy=true

Make sure the shared runner can discover queue files in:

`docs/chatgpt_status/<PAGE_KEY>/queue/*.json`

When a new ChatGPT page creates a queue with this template, the same single runner must pick it up.

## AAYS1 security task must remain the active test

PAGE_KEY:

`aays1`

Current queue:

`docs/chatgpt_status/aays1/queue/0000_115_security_batch_join_backoff_force_pickup.task.json`

Expected output:

`docs/chatgpt_status/security_public_safety/runner_outputs/115_security_batch_join_backoff.json`

Current metrics must not be increased until output exists:

- completion_percent=92
- remaining_percent=8
- verified_parcels=9
- total_parcels=1264
- final_ready=false

## Acceptance test

After implementing, run locally:

`START_AAYS_SINGLE_RUNNER_AND_PANEL.cmd`

Then verify:

1. One panel window opens.
2. Exactly one runner lock exists.
3. Shared heartbeat updates under `_shared/heartbeat`.
4. Shared latest status updates under `_shared/status`.
5. aays1 queue is no longer skipped as INVALID_QUEUE_CONTRACT.
6. If the runner starts the task, page heartbeat/status/report files are created.
7. If output is missing, final_ready remains false and blocker is written.
8. If output is created, metrics are updated only from real output.
9. GitHub/main push succeeds.

Write final acceptance report to:

`docs/chatgpt_status/_shared/reports/AAYS_SINGLE_RUNNER_PANEL_ACCEPTANCE_LATEST.md`

The final report must include:

- runner_active true/false
- panel_opened true/false
- single_runner_lock_ok true/false
- heartbeat_updated true/false
- aays1_queue_contract_valid true/false
- aays1_queue_started true/false
- expected_output_found true/false
- final_ready false unless real gates pass
- blockers list
- exact files changed
