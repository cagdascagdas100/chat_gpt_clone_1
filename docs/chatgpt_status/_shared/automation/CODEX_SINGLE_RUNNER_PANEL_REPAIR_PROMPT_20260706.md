# Codex Prompt: AAYS single canonical runner repair and panel

Repo: cagdascagdas100/chat_gpt_clone_1
Branch: codex/aays-single-runner-v5-20260706
Primary local root: C:\AAYS_WT\AAYS_REPAIR_20260706_1738
Page key: aays1

Goal: keep exactly one shared/canonical AAYS runner. Do not create parallel runner loops. Repair the current runner so queue/status/report/heartbeat/completed flow continues with GitHub evidence.

Current proven blockers:
- V5 runner starts but fails at controller git fetch with Out of memory malloc.
- A later local run wrote local status/report/log files but could not push because there were unstaged changes and branch was behind remote.
- Latest GitHub status still shows queue_seen=false, queue_started=false, runner_output_uploaded=false, PUSH_SYNC_OK=false, final_ready=false.

Required Codex work:
1. Patch the canonical runner Git calls to use low-memory git settings internally for fetch, pull, rebase, and push.
2. Use fetch --no-tags where possible and avoid full-history fetch when not needed.
3. If fetch still fails, write a structured blocker status/report without fake completed or fake final_ready.
4. Fix runtime summary push so local runtime files are staged/committed safely before rebase/push, while unscoped dirty files block execution with CONTROLLER_DIRTY_NO_RUN.
5. Preserve allowed_paths enforcement for actual task output.
6. Create one user-click launcher: docs/chatgpt_status/_shared/automation/AAYS_SINGLE_RUNNER_START.cmd
7. Create one launcher script: docs/chatgpt_status/_shared/automation/START_AAYS_SINGLE_RUNNER_WITH_PANEL_20260706.ps1
8. The launcher must open the canonical runner and a local panel, and must refuse to start a second active runner if a fresh lock/heartbeat exists.
9. Create panel files under docs/chatgpt_status/_shared/panel/. The panel must show five menu placeholders until the user provides names from a photo: MENU_1_FROM_PHOTO through MENU_5_FROM_PHOTO.
10. Panel must show Runner aktif only when the canonical runner heartbeat is fresh and queue/status flow is healthy. Otherwise show Runner problemli and the blocker.
11. Panel must show progress percentage from real status/completed/blocked/report evidence only. Never show fake 100 percent.
12. Add templates for new ChatGPT pages under docs/chatgpt_status/_shared/templates/ so new pages write queue files for the same runner instead of starting another runner.

Safety rules:
- fake_data=false
- db_write=false
- ddl=false
- migration=false
- production_deploy=false
- final_ready=false unless real final criteria are proven
- no fake completed
- no fake percent 100

Required Codex result file:
docs/chatgpt_status/_shared/status/codex_single_runner_panel_repair_result_20260706.json

The result JSON must list files_created, files_modified, runner_script_path, launcher paths, panel path, template path, single_runner_enforced, panel_opens_with_runner, oom_fetch_handled, dirty_tree_handled, final_ready=false, and blockers.
