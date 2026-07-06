# Codex Task — AAYS Single Canonical Runner + Visible Panel + New ChatGPT Page Pickup

Use this file as the exact Codex handoff prompt. Work in the existing repository and continue the current AAYS/TerraYield runner system. Do not create a parallel runner.

## Repository

```text
Repo local root expected by user:
C:\Users\cagda\Documents\GitHub\AAYS

Known GitHub repo used in current evidence:
cagdascagdas100/chat_gpt_clone_1

Branch:
main
```

If the local checkout is actually `F:\chatgpt\chat_gpt_clone_1_main`, support that too, but the user-facing one-click file must work from `C:\Users\cagda\Documents\GitHub\AAYS` when that folder contains `docs\chatgpt_status`.

## User goal

The user wants exactly one runner. When the user clicks one command file, the same runner process should open and continue the same queue/status/report/heartbeat/completed workflow. If the user opens a new ChatGPT page later, the files must already be prepared so that the same runner can pick up the new page queue. When the runner starts, a visible panel window must also open. The panel will have five menu names; the user will provide a photo later. Until then use placeholders and make the menu names configurable in one small JSON file.

## Critical rules

```text
Do not start a new parallel runner.
Do not create fake completed evidence.
Do not set final_ready=true without real gate evidence.
Do not write fake percent 100.
Do not fabricate rows, source_url, source_date, browser proof, or production evidence.
Do not write outside allowed_paths for page tasks.
Do not perform DB write, DDL, migration, or production deploy.
If proof is missing, write blocker and keep final_ready=false.
```

## Known current runner problem

GitHub evidence shows the shared runner heartbeat/status is stale:

```text
docs/chatgpt_status/_shared/heartbeat/MULTI_PAGE_heartbeat_latest.json
started_at: 2026-07-05T16:34:06Z
runner: RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_V3_20260705

docs/chatgpt_status/_shared/status/MULTI_PAGE_latest_status.json
checked_at: 2026-07-05T16:34:07Z
queue_started: false
task_runs_in_clean_worktree: false
allowed_paths_enforced: false
runner_output_uploaded: false
post_sync_ok: false
PUSH_SYNC_OK: false
```

There is also a known V4 clone argument bug from previous manual runs:

```text
Bad line pattern:
Invoke-AaysGit $WorkRoot -c core.longpaths=true clone --branch $Task.target_branch --single-branch $url $worktree

Observed failure:
Cannot find path 'core.longpaths=true' because it does not exist.
```

The previous temporary workaround replaced that line with:

```text
Invoke-AaysGit $WorkRoot clone --branch $Task.target_branch --single-branch $url $worktree
```

Codex must make this permanent in a new safe runner version and update the canonical wrapper to point to it.

## Files to read first

Read these before changing anything:

```text
docs/chatgpt_status/_shared/contracts/AAYS_SINGLE_RUNNER_PAGE_CONTRACT_20260706.md
docs/chatgpt_status/_shared/templates/NEW_CHATGPT_PAGE_QUEUE_TEMPLATE_20260706.json
docs/chatgpt_status/_shared/panel/page_status_index_schema_20260706.json
docs/chatgpt_status/_shared/status/runner_problem_user_action_required_20260706_001.json
docs/chatgpt_status/_shared/status/runner_still_stale_after_devam_20260706_002.json
docs/chatgpt_status/topography/status/topography_resume_prompt_context_blocker_20260706_001.json
```

If any file is missing, continue with available files and write a blocker; do not claim completed.

## Required implementation

### 1. Make one canonical runner version

Create or update a permanent runner script:

```text
docs/chatgpt_status/_shared/automation/RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_V5_20260706.ps1
```

Requirements:

```text
- Fix the V4 clone argument bug permanently.
- Use a short worktree root by default, for example C:\AAYS_WT or F:\AAYS_WT.
- Support RepoRoot parameter.
- Support RepoFullName parameter.
- Support MainBranch parameter.
- Support WorkRoot parameter.
- Support MaxTasks parameter.
- Support StaleMinutes parameter.
- Enforce one shared lock only.
- Validate queue contract before running.
- Skip invalid legacy queues with clear validation errors.
- Never execute queues missing safety flags.
- Write shared heartbeat/status after every run attempt, even when no task is processed.
- Write task-level started/gate/completed/report/heartbeat when a task runs.
- Keep final_ready=false unless real gates pass.
```

Then update the canonical wrapper:

```text
docs/chatgpt_status/_shared/automation/RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER.ps1
```

to call V5. Do not leave the wrapper pointing to V3 or a broken V4.

### 2. Create one-click starter file

Create a user-facing command file at repo root:

```text
START_AAYS_CANONICAL_RUNNER_AND_PANEL.cmd
```

This file must:

```text
- Start exactly one visible runner console.
- Use the local repo root where the file lives when possible.
- Validate that docs\chatgpt_status exists.
- Start the canonical runner loop.
- Open the visible panel window.
- Keep the console open and readable.
- Print errors clearly.
```

Also create the PowerShell implementation it calls:

```text
docs/chatgpt_status/_shared/automation/START_AAYS_CANONICAL_RUNNER_AND_PANEL_20260706.ps1
```

This script may open a second visible panel window, but it must not start a second runner.

### 3. Create visible panel

Create a panel HTML file:

```text
docs/chatgpt_status/_shared/panel/aays_single_runner_panel.html
```

and a config file:

```text
docs/chatgpt_status/_shared/panel/aays_single_runner_panel_menu_config.json
```

The menu config must initially contain five placeholders because the user will send a photo later:

```json
{
  "menus": [
    { "id": "menu_1", "label": "PHOTO_PENDING_MENU_1" },
    { "id": "menu_2", "label": "PHOTO_PENDING_MENU_2" },
    { "id": "menu_3", "label": "PHOTO_PENDING_MENU_3" },
    { "id": "menu_4", "label": "PHOTO_PENDING_MENU_4" },
    { "id": "menu_5", "label": "PHOTO_PENDING_MENU_5" }
  ]
}
```

When the photo is supplied later, update only this config file with the real five menu names.

Panel must show:

```text
- Runner status: RUNNER AKTIF or PROBLEM
- Last shared heartbeat timestamp
- Last shared status timestamp
- PUSH_SYNC_OK
- queue_started
- processed task count
- skipped invalid queue count
- final_ready status
- blockers
- page list from page_status_index_latest.json
- per-page completion_percent and remaining_percent
- per-page final_ready
- per-page latest task id
- per-page latest heartbeat/completed evidence path
```

Panel should auto-refresh. If loaded directly from file and browser blocks local JSON reads, the starter script should run a minimal local static file server only for panel files, for example under port 8765. This is a UI server only, not a second runner.

Panel status logic:

```text
RUNNER AKTIF only if shared heartbeat/status is fresh and PUSH_SYNC_OK=true or the latest task-level runner output is fresh.
PROBLEM if heartbeat is stale, status is stale, queue cannot start, PUSH_SYNC_OK=false, lock is stale, or required files are missing.
```

### 4. Generate panel latest index

Create/update:

```text
docs/chatgpt_status/_shared/panel/page_status_index_latest.json
```

It must be generated from `docs/chatgpt_status/<PAGE_KEY>/` folders. Treat every direct child of `docs/chatgpt_status/` except `_shared` as a page candidate.

Each page entry must include:

```json
{
  "page_key": "example_page_key",
  "display_name": "Example Page",
  "latest_queue_status": "queued|running|done|blocked|failed|unknown",
  "latest_task_id": "stable-task-id",
  "completion_percent": 0,
  "remaining_percent": 100,
  "final_ready": false,
  "last_heartbeat_at": null,
  "last_completed_at": null,
  "blockers": [],
  "evidence_paths": [],
  "runner_contract_valid": true,
  "queue_contract_errors": []
}
```

Use existing task-level evidence when available. Do not invent completion.

### 5. New ChatGPT page pickup

Make sure this template exists and is complete:

```text
docs/chatgpt_status/_shared/templates/NEW_CHATGPT_PAGE_QUEUE_TEMPLATE_20260706.json
```

Also create a human prompt file:

```text
docs/chatgpt_status/_shared/templates/NEW_CHATGPT_PAGE_CONTINUE_PROMPT_20260706.md
```

It must tell a new ChatGPT page to:

```text
- Set PAGE_KEY.
- Read the shared contract.
- Create only its own page queue under docs/chatgpt_status/<PAGE_KEY>/queue/.
- Do not start a new runner.
- Use the existing canonical runner.
- Write blocker if evidence is missing.
- Keep final_ready=false until real evidence gates pass.
```

### 6. Queue/status/report/heartbeat/completed evidence for this repair

Create a repair queue under shared:

```text
docs/chatgpt_status/_shared/queue/single_runner_panel_repair_20260706.json
```

Use the same queue contract shape, with allowed_paths limited to:

```text
docs/chatgpt_status/_shared/
START_AAYS_CANONICAL_RUNNER_AND_PANEL.cmd
```

During or after the repair, write:

```text
docs/chatgpt_status/_shared/status/single_runner_panel_repair_20260706_started.json
docs/chatgpt_status/_shared/status/single_runner_panel_repair_20260706_gate.json
docs/chatgpt_status/_shared/status/single_runner_panel_repair_20260706_completed.json
docs/chatgpt_status/_shared/completed/single_runner_panel_repair_20260706_completed.json
docs/chatgpt_status/_shared/reports/single_runner_panel_repair_20260706_report.md
docs/chatgpt_status/_shared/heartbeat/single_runner_panel_repair_20260706_heartbeat.txt
```

If local execution cannot be verified, do not write completed as success. Write blocked evidence instead:

```text
docs/chatgpt_status/_shared/blocked/single_runner_panel_repair_20260706_blocked.json
```

### 7. Acceptance criteria

The repair is accepted only if all are true:

```text
- START_AAYS_CANONICAL_RUNNER_AND_PANEL.cmd exists at repo root.
- Running it opens exactly one runner console.
- Running it opens a visible panel window.
- Canonical wrapper points to V5, not V3 or broken V4.
- Shared heartbeat/status update after runner starts.
- Panel shows RUNNER AKTIF when runner evidence is fresh.
- Panel shows PROBLEM when runner evidence is stale or push failed.
- Panel lists all page_key entries discovered from docs/chatgpt_status/.
- New ChatGPT page template exists.
- No fake completed/final_ready/%100 is written.
```

## Five menu names

The user will send a photo later. Until then do not guess menu names. Use these placeholders:

```text
PHOTO_PENDING_MENU_1
PHOTO_PENDING_MENU_2
PHOTO_PENDING_MENU_3
PHOTO_PENDING_MENU_4
PHOTO_PENDING_MENU_5
```

When the photo arrives, update:

```text
docs/chatgpt_status/_shared/panel/aays_single_runner_panel_menu_config.json
```

Only replace labels. Do not alter runner logic just to change menu names.

## Final Codex response format

When done, respond with:

```text
Runner repair status: done / blocked / partial
Panel status: done / blocked / partial
One-click file: <path>
Canonical runner: <path>
Panel file: <path>
New page template: <path>
Completed percent: <number>%
Remaining percent: <number>%
Final ready: false unless all gates prove true
Blockers:
- <blocker>
Evidence files:
- <path>
- <path>
- <path>
User wait: <minutes> minutes
```

Do not claim success unless the repo contains evidence files and the runner heartbeat/status updates after local launch.
