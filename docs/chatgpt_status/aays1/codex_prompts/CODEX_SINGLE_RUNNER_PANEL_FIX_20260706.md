# Codex Task: Single Shared Runner + Control Panel + Reboot Launcher Fix

Repo: `cagdascagdas100/chat_gpt_clone_1`
Branch: `main`
Active page key: `aays1`
Current layer: `security_public_safety`
Current task queue: `docs/chatgpt_status/aays1/queue/0000_115_security_batch_join_backoff_force_pickup.task.json`
Current expected output: `docs/chatgpt_status/security_public_safety/runner_outputs/115_security_batch_join_backoff.json`

## Problem to fix

The current ChatGPT page keeps verifying the same valid queue, but GitHub still has no fresh shared runner pickup/output evidence for task 115.

Known evidence state:

- The 115 queue is now structurally valid and pending.
- The shared heartbeat/status still points to an old V3 cycle.
- The task heartbeat is missing.
- The script heartbeat is missing.
- The task completed marker is missing.
- The expected runner output `115_security_batch_join_backoff.json` is missing.
- No metric may be increased until a real GitHub-visible runner output is present.
- Do not write fake `completed`, fake `final_ready=true`, or fake `%100`.

## Non-negotiable rules

1. Keep exactly one shared/canonical runner.
2. Do not create or start parallel page-specific runners.
3. All ChatGPT pages must write queue/status/report/heartbeat/completed files that the same shared runner can process.
4. Enforce `allowed_paths` for each task.
5. Keep `no_fake_final_ready=true`, `no_db_write=true`, `no_migration=true`, `no_production_deploy=true` on queue tasks.
6. Do not perform DB writes, migrations, DDL, or production deploy.
7. If evidence is missing, write a blocker/status file and keep `final_ready=false`.
8. If the runner is active and healthy, the panel must show `runner aktif`.
9. If the runner is not active or not processing, the panel must show the exact problem, not a fake success.

## Existing canonical files to preserve and use

- Runner wrapper: `docs/chatgpt_status/_shared/automation/RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER.ps1`
- Runner V4: `docs/chatgpt_status/_shared/automation/RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_V4_20260706.ps1`
- Page registry: `docs/chatgpt_status/_shared/contracts/PAGE_KEY_REGISTRY.json`
- Queue contract: `docs/chatgpt_status/_shared/contracts/SINGLE_SHARED_RUNNER_CONTRACT.md`
- Page panel index: `docs/chatgpt_status/_shared/status/page_panel_index.json`
- Shared heartbeat: `docs/chatgpt_status/_shared/heartbeat/MULTI_PAGE_heartbeat_latest.json`
- Shared latest status: `docs/chatgpt_status/_shared/status/MULTI_PAGE_latest_status.json`

## Required implementation

Create or update the following shared launcher/panel system. Use the repo's existing style and keep all writes Git-safe.

### 1. One double-click launcher

Create a single user-facing launcher file, preferably:

- `START_AAYS_SINGLE_RUNNER_PANEL.cmd`

The user must be able to double-click this file after reboot. It must:

1. Set the correct repo root.
2. Pull/sync `main` safely, without destroying non-runtime user changes.
3. Start the canonical shared runner only if no healthy shared runner is already active.
4. Never start a second runner if a valid lock/fresh heartbeat exists.
5. Open the runner control panel window.
6. Write local start status to shared status paths.
7. Leave clear error text if PowerShell execution policy, git pull, lock, path, or runner health fails.

### 2. Runner supervisor script

Create or update a supervisor script, preferably:

- `docs/chatgpt_status/_shared/automation/START_AAYS_SINGLE_RUNNER_PANEL.ps1`

Responsibilities:

- Locate repo root.
- Validate `git`, `powershell`, repo path, branch, and runner files.
- Read `PAGE_KEY_REGISTRY.json`.
- Validate all pending queue files before invoking the shared runner.
- Start only `RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER.ps1`.
- Verify fresh heartbeat after start.
- If runner cannot start, write a blocker/status file under `_shared/status` and show the problem in the panel.
- Keep a strict single-runner lock.
- Support reboot usage: the same `.cmd` must be enough after Windows restart.

### 3. Control panel window

Create a panel window, preferably PowerShell WinForms/WPF or a local HTML file opened from the launcher.

Panel requirements:

- It opens automatically when `START_AAYS_SINGLE_RUNNER_PANEL.cmd` is clicked.
- It has five menu slots. The user will later provide a photo with the exact five menu names. Until names are provided, read them from a config file and use placeholders.
- Store menu config at:
  - `docs/chatgpt_status/_shared/panel/menu_config.json`
- Suggested placeholder config:
  - `menu_1`
  - `menu_2`
  - `menu_3`
  - `menu_4`
  - `menu_5`
- When the user provides menu names, only update the config, not the runner core.

Panel must show:

- Runner status: `runner aktif`, `runner bekliyor`, or problem code.
- Active task id.
- Active page key.
- Queue status.
- Last heartbeat time.
- Expected output path.
- Completed marker path.
- Blocker text if any.
- Overall progress percent for each page.
- Current `aays1` metrics: `%92` complete, `%8` remaining, `9/1264` verified until real output updates it.

### 4. New ChatGPT page compatibility

Create/update a new-page continuation template so every new ChatGPT page writes compatible queue/status/report files for this same shared runner. Prefer:

- `docs/chatgpt_status/_shared/templates/NEW_CHATGPT_PAGE_CONTINUATION_TEMPLATE.md`

The template must instruct new pages to:

- Use the existing repo and branch.
- Choose or declare one `page_key`.
- Write queue files only under `docs/chatgpt_status/<PAGE_KEY>/queue/`.
- Include `task_id`, `page_key`, `status`, `target_branch`, `script_path`, `expected_output`, `allowed_paths`, `no_fake_final_ready`, `no_db_write`, `no_migration`, `no_production_deploy`, `fake_data=false`, `final_ready=false`.
- Never create a separate runner.
- Let the single shared runner pick up the task.
- Write blockers when evidence is missing.

### 5. Health-check and acceptance

Implement a health check command inside the launcher or supervisor.

It must verify:

- Single runner lock is present only when valid.
- Heartbeat is fresh or stale with a clear problem.
- `MULTI_PAGE_latest_status.json` is updated after runner start.
- A valid pending queue can be seen.
- Invalid queues are reported with exact validation errors.
- The current 115 task is either picked up or blocked with explicit reason.
- No fake completed or final-ready markers are produced.

Acceptance criteria:

- Double-clicking `START_AAYS_SINGLE_RUNNER_PANEL.cmd` starts/attaches to one shared runner and opens the panel.
- Rebooting Windows and double-clicking the same file works again.
- If runner is healthy, panel says `runner aktif`.
- If runner is not healthy, panel shows the real blocker.
- New ChatGPT pages can add queue files and the same runner can continue them.
- The panel reads from GitHub-synced repo files and shows page progress.
- No metric is increased unless a real runner output/completed marker is present.

## Start with these concrete fixes

1. Add `START_AAYS_SINGLE_RUNNER_PANEL.cmd`.
2. Add `docs/chatgpt_status/_shared/automation/START_AAYS_SINGLE_RUNNER_PANEL.ps1`.
3. Add `docs/chatgpt_status/_shared/panel/menu_config.json` with five placeholder menu names.
4. Add the panel renderer script/file.
5. Add or fix `NEW_CHATGPT_PAGE_CONTINUATION_TEMPLATE.md`.
6. Run a read-only/safe validation and write a status report.
7. Do not mark 115 complete unless the real 115 output exists.

## Current blocker to resolve

`aays1` / 115 is waiting because the queue is pending but the GitHub-visible shared runner output has not appeared. Codex should fix the launcher/supervisor/panel flow so the user can start the canonical runner locally with one click and see whether the runner is active or blocked.
