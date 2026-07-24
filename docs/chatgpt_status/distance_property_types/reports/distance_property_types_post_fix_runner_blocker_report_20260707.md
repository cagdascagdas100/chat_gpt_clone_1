# Distance Property Types - Post-Fix Runner Blocker Report - 20260707

PAGE_KEY: distance_property_types
Branch: codex/aays-single-runner-v5-20260706
Repo root: C:\AAYS_WT\AAYS_REPAIR_20260706_1738
Runner contract: docs/chatgpt_status/_shared/automation/RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_STABLE_20260707.ps1
Last known runner fix commit: 4cdb83f96

## Short status

Post-fix GitHub evidence is still missing for a healthy stable runner cycle. Do not treat the runner as healthy yet.

## Evidence checked from GitHub

1. Fix commit exists.
   - Commit 4cdb83f96: Fix stable runner git safe directory handling.
   - It injects safe.directory values into each runner git call.
   - It reports local verification: parser check passed and one-shot -NoPush -ScanOnly returned exit_code=0.

2. Bootstrap status is stale for the post-fix requirement.
   - docs/chatgpt_status/_shared/status/runner_bootstrap_latest.json still has updated_at=2026-07-07T09:15:54Z.
   - It still reports scan_runner=RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_V5_20260706.
   - User asked to trust only stable daemon evidence after 2026-07-07 15:33:19Z.

3. Stable daemon status is stale and still failing.
   - docs/chatgpt_status/_shared/status/stable_runner_daemon_latest.json has checked_at=2026-07-07T00:58:43Z.
   - It reports runner_exit_code=1.
   - Its output tail reports runner_output_uploaded=false, post_sync_ok=false, PUSH_SYNC_OK=false.
   - Blockers include CONTROLLER_DIRTY_SYNC_SKIPPED and RUNNER_TASK_FAILED.

4. distance_property_types queue remains pending.
   - Queue file: docs/chatgpt_status/distance_property_types/queue/distance_property_types_site_check_20260703_0950.task.json.
   - Status is queued.
   - The queue expects runner output at docs/chatgpt_status/distance_property_types/runner_outputs/distance_property_types_site_check_20260703_0950.report.json.

5. distance_property_types post-run evidence is missing.
   - status file is missing.
   - heartbeat file is missing.
   - expected runner output report is missing / 404.
   - progress report says final_ready=false and evidence_rows=0.

## Current blocker

The fix commit may have fixed Git safe.directory locally, but the GitHub repo does not yet show a post-fix healthy runner cycle after 2026-07-07 15:33:19Z. Therefore ChatGPT pages cannot safely start real tasks or increase metrics.

## Required Codex action

1. Run only the existing stable shared runner. Do not create a new runner.
2. Ensure START_AAYS_RUNNER.bat actually launches docs/chatgpt_status/_shared/automation/RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_STABLE_20260707.ps1, not the old V5 runner.
3. Push/update fresh GitHub evidence after 2026-07-07 15:33:19Z:
   - docs/chatgpt_status/_shared/status/runner_bootstrap_latest.json
   - docs/chatgpt_status/_shared/status/stable_runner_daemon_latest.json
   - docs/chatgpt_status/_shared/reports/MULTI_PAGE_runner_output_<new_run_id>.json
4. Required healthy shared-runner markers:
   - runner_exit_code=0
   - queue_seen=true
   - single_runner_lock_acquired=true or RUNNER_ALREADY_ACTIVE only if truly live and fresh
   - runner_output_uploaded=true
   - post_sync_ok=true
   - PUSH_SYNC_OK=true
   - CONTINUE_RUNNER_READY=true
   - final_ready=false unless evidence gates pass
   - fake_data=false
   - db_write=false
   - migration=false
   - production_deploy=false
5. Then verify distance_property_types pickup by producing or confirming:
   - docs/chatgpt_status/distance_property_types/status/distance_property_types_site_check_20260703_0950.status.json
   - docs/chatgpt_status/distance_property_types/heartbeat/distance_property_types_site_check_20260703_0950.heartbeat.json
   - docs/chatgpt_status/distance_property_types/runner_outputs/distance_property_types_site_check_20260703_0950.report.json
6. If distance_property_types has no evidence input rows, do not complete it as final. Write blocked or completed_no_real_evidence_rows with final_ready=false.

## Do not do

- Do not start a parallel runner.
- Do not make F: canonical.
- Do not write fake completed.
- Do not write fake percent 100.
- Do not set final_ready=true without GitHub-visible evidence.
- Do not run DB write, migration, or production deploy.
