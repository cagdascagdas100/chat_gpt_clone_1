# Codex Task: AAYS Single Runner + Panel Stabilization

Repo: `cagdascagdas100/chat_gpt_clone_1`
Branch: `codex/aays-single-runner-v5-20260706`
Primary local clone: `C:\AAYS_WT\AAYS_REPAIR_20260706_1738`

## Non-negotiable rules

- Maintain exactly one canonical/shared runner. Do not create page-specific or parallel runner processes.
- Do not write fake completion, fake heartbeat, fake browser proof, fake final_ready, or fake percent 100.
- Keep `final_ready=false` unless real acceptance evidence exists.
- Do not perform DB writes, migrations, DDL, production deploys, or production imports.
- Do not delete project files. If local runtime outputs block a clean run, stash or archive them safely with an explicit name.
- All ChatGPT page queues must be able to continue through this one runner when a new ChatGPT page is opened and writes queue/status files.

## Current confirmed blockers from local logs

1. The old V5 runner failed before branch detection because `Invoke-Git` tried to use `$script:GitLogPath` before it was initialized.
   - Local patch inserted a pre-init fallback around `AAYS_git_preinit_V5.log`.
   - Verify this exists in `docs/chatgpt_status/_shared/automation/RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_V5_20260706.ps1`.

2. Git memory/OOM happened during fetch/push:
   - `fatal: Out of memory, malloc failed (tried to allocate 524288000 bytes)`.
   - Local mitigation was applied: `pack.threads=1`, `pack.windowMemory=16m`, `pack.packSizeLimit=64m`, `core.bigFileThreshold=1m`, `gc.auto=0`, `http.postBuffer=1048576000`, then `git gc --prune=now`.
   - Codex should make the launcher apply safe local git config before runner execution.

3. The latest runner advanced past the null-path issue and then stopped at:
   - `CONTROLLER_DIRTY_NO_RUN`
   - `BLOCKED_UNSCOPED_CHANGES`
   Dirty files were runtime/status outputs under page folders, for example:
   - `docs/chatgpt_status/aays1/blocked/...`
   - `docs/chatgpt_status/aays1/heartbeat/...`
   - `docs/chatgpt_status/aays1/reports/...`
   - `docs/chatgpt_status/aays1/status/...`
   - `docs/chatgpt_status/security_public_safety/runner_outputs/...`
   - `docs/chatgpt_status/security_public_safety/status/...`

## Required implementation

Create or update a single user-launchable entry point:

- Preferred path: `RUN_AAYS_SINGLE_RUNNER_PANEL.cmd` at repo root.
- It must call a PowerShell launcher, for example:
  `docs/chatgpt_status/_shared/automation/START_AAYS_SINGLE_RUNNER_PANEL_20260706.ps1`

When the user double-clicks the `.cmd`, it must:

1. Open exactly one runner process/window.
2. Open one panel/status window at the same time.
3. Apply safe local git memory config before any fetch/push.
4. Verify repo branch is `codex/aays-single-runner-v5-20260706` unless explicitly overridden.
5. Prevent duplicate runner startup if the canonical lock says a runner is active.
6. If runner is not working, show the exact blocker/problem in the panel.
7. If runner is working and able to process continuation tasks, show `RUNNER AKTIF` / `runner active` in the panel.
8. Show percent/progress from real status files only. Do not invent percentages.
9. On Windows restart, the same `.cmd` must still be enough to resume the single runner and panel.

## Panel requirements

The panel must show five menu labels. The user will provide the exact names by photo. Until then, implement placeholders in a configurable JSON file, for example:

`docs/chatgpt_status/_shared/panel/menu_config.json`

with fields:

```json
{
  "menus": [
    "MENU_1_FROM_USER_PHOTO",
    "MENU_2_FROM_USER_PHOTO",
    "MENU_3_FROM_USER_PHOTO",
    "MENU_4_FROM_USER_PHOTO",
    "MENU_5_FROM_USER_PHOTO"
  ]
}
```

The panel must read current runner state from real files, including:

- `docs/chatgpt_status/_shared/status/MULTI_PAGE_latest_status.json`
- `docs/chatgpt_status/_shared/status/queue_selection_debug_20260706_v5.json`
- `docs/chatgpt_status/_shared/heartbeat/MULTI_PAGE_heartbeat_latest.json`
- page-level completed/blocked/status/report outputs under `docs/chatgpt_status/<PAGE_KEY>/...`

## Runner repair requirements

Update `RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_V5_20260706.ps1` so it is robust for local use:

1. `Invoke-Git` must not fail when `$script:GitLogPath` is not initialized.
2. `Invoke-Git` must explicitly reject null/empty cwd with `BLOCKED_NULL_GIT_CWD`.
3. Before controller dirty-check blocks execution, runtime-only dirty files should be safely stashed or handled as runtime noise, not deleted.
4. Runtime-only dirs should include both `_shared` runtime dirs and page runtime dirs:
   - `docs/chatgpt_status/_shared/status/`
   - `docs/chatgpt_status/_shared/heartbeat/`
   - `docs/chatgpt_status/_shared/logs/`
   - `docs/chatgpt_status/_shared/reports/`
   - `docs/chatgpt_status/_shared/runner_lock/`
   - `docs/chatgpt_status/*/status/`
   - `docs/chatgpt_status/*/heartbeat/`
   - `docs/chatgpt_status/*/reports/`
   - `docs/chatgpt_status/*/runner_outputs/`
   - `docs/chatgpt_status/*/blocked/`
   - `docs/chatgpt_status/*/completed/`
5. Non-runtime dirty files must still block with a precise list. Do not auto-stash source code or data files.
6. Scan-only and no-task cases must still write/push real status/debug outputs so ChatGPT can verify whether the runner ran.
7. If push/fetch fails, write a local status JSON with the exact Git failure and keep final_ready=false.

## Acceptance criteria

After implementation, from `C:\AAYS_WT\AAYS_REPAIR_20260706_1738`, the following must work:

```powershell
.\RUN_AAYS_SINGLE_RUNNER_PANEL.cmd
```

Expected real outcomes:

- Exactly one canonical runner starts.
- A panel/status window opens.
- Panel shows the five menu labels from config.
- Panel shows either exact blockers or `RUNNER AKTIF`.
- `queue_selection_debug_20260706_v5.json` is created/updated after a scan.
- `MULTI_PAGE_latest_status.json` is created/updated after a scan.
- If ready queue exists, one task is processed by the single runner.
- If no queue exists, panel says no ready queue and does not fake completion.
- `fake_data=false`, `db_write=false`, `ddl=false`, `migration=false`, `production_deploy=false` remain visible in all summary outputs.
- Do not mark product/task final unless real proof exists.

## Deliverables

Codex should create/update these files and commit them on the same branch:

- `RUN_AAYS_SINGLE_RUNNER_PANEL.cmd`
- `docs/chatgpt_status/_shared/automation/START_AAYS_SINGLE_RUNNER_PANEL_20260706.ps1`
- `docs/chatgpt_status/_shared/automation/RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_V5_20260706.ps1`
- `docs/chatgpt_status/_shared/panel/menu_config.json`
- `docs/chatgpt_status/_shared/panel/README_SINGLE_RUNNER_PANEL_20260706.md`

## Final report required from Codex

Codex must report:

- Files changed.
- Exact commands tested.
- Whether runner window opened.
- Whether panel window opened.
- Whether duplicate-runner protection worked.
- Current blocker if runner is not active.
- Real status file paths updated.
- `final_ready` value and why.
