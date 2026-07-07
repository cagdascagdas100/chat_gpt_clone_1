# Distance Property Types - Codex Runner Health Blocker Report - 20260707

PAGE_KEY: distance_property_types
Branch: codex/aays-single-runner-v5-20260706
Repo root expected: C:\AAYS_WT\AAYS_REPAIR_20260706_1738

## Current GitHub-proven status

- runner_bootstrap_latest.json says runner_status=runner_started and runner_lock_active=true.
- stable_runner_daemon_latest.json says status=runner_loop_completed but runner_exit_code=1.
- Shared runner output report exists for run_id=20260707_035718, but it reports runner_output_uploaded=false, post_sync_ok=false, PUSH_SYNC_OK=false.
- Shared report blockers are CONTROLLER_DIRTY_SYNC_SKIPPED and RUNNER_TASK_FAILED.
- The processed task in the failed shared report is page_key=aays1 / task_id=normalized-065-progress-report-20260706, not distance_property_types.
- distance_property_types expected runner output is missing on GitHub: docs/chatgpt_status/distance_property_types/runner_outputs/distance_property_types_site_check_20260703_0950.report.json.

## Root cause hypothesis from repo evidence

The stable runner starts and acquires the single-runner lock, but it does not complete a healthy GitHub-synced cycle because the controller/worktree becomes dirty and the runner refuses to pull/push non-destructively. The failing task writes queue/status/heartbeat/report files, then Stage-AllowedOnly blocks on paths outside that task allowed scope. Because Push-Sync is not reached successfully, runner_output_uploaded and PUSH_SYNC_OK remain false.

A second mismatch exists: the user-facing stable contract names RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_STABLE_20260707, but runner_bootstrap_latest.json still reports scan_runner=RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_V5_20260706. Confirm the launcher is invoking the intended stable runner and that all status files report the same runner name.

## Required Codex fix

1. Do not start a new/parallel runner.
2. Keep canonical repo root as C:\AAYS_WT\AAYS_REPAIR_20260706_1738, not F:.
3. Patch the stable runner/controller so runtime-generated shared files are either safely restored/stashed before sync or explicitly classified as controller runtime, before pull/rebase/push.
4. Prevent one page task, especially aays1 normalized-065-progress-report-20260706, from blocking all other page queues when it has unscoped/dirty files.
5. When a task is dirty/unscoped, write a page-local blocked/skipped_obsolete report with final_ready=false, then move to the next queued task rather than leaving the whole runner unhealthy.
6. Ensure the runner can complete one full cycle with: queue_seen=true, queue_started=true, single_runner_lock_acquired=true, allowed_paths_enforced=true, runner_output_uploaded=true, post_sync_ok=true, PUSH_SYNC_OK=true, CONTINUE_RUNNER_READY=true, final_ready=false unless evidence gates pass.
7. After the fix, verify distance_property_types by producing or confirming this file on GitHub: docs/chatgpt_status/distance_property_types/runner_outputs/distance_property_types_site_check_20260703_0950.report.json.

## Do not do

- Do not write fake completed.
- Do not write fake percent 100.
- Do not set final_ready=true without real evidence rows and GitHub-visible runner output.
- Do not run DB write, migration, or production deploy.
- Do not make F: canonical.
