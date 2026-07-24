# Distance Property Types - Runner Pickup Root Cause Report - 20260707

PAGE_KEY: distance_property_types
Repo: C:\AAYS_WT\AAYS_RUNNER_CLEAN_20260707
Branch: codex/aays-single-runner-v5-20260706
Runner: docs/chatgpt_status/_shared/automation/RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_STABLE_20260707.ps1
Launcher: C:\Users\cagda\Documents\GitHub\AAYS\START_AAYS_RUNNER.bat

## Exact problem

The stable runner itself is now healthy, but distance_property_types has not been picked up yet after its queue was fixed.

This is not the old V5 problem anymore. The current blocker is pickup evidence missing after the queue-format correction.

## Evidence

1. Shared runner health evidence is good:
   - runner_bootstrap_latest.json shows repo_root=C:\AAYS_WT\AAYS_RUNNER_CLEAN_20260707.
   - runner_status=runner_active.
   - runner_engine=stable_legacy_worktree_runner_20260707.
   - scan_runner=RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_STABLE_20260707.
   - CONTINUE_RUNNER_READY=true.
   - fake_data=false, db_write=false, migration=false, production_deploy=false.

2. Stable daemon evidence is good:
   - stable_runner_daemon_latest.json checked_at=2026-07-07T18:25:07Z.
   - runner_exit_code=0.
   - scan_runner=RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_STABLE_20260707.
   - controller_sync_ok=true.
   - blockers=[] in runner output tail.

3. distance_property_types queue was invalid before because required runner safety flags existed only under nested safety, not as top-level fields.
   - The stable runner Parse-Queue validates top-level no_fake_final_ready, no_db_write, no_migration, no_production_deploy.
   - That caused distance_property_types to be excluded from ready queue even though status=queued.

4. ChatGPT fixed the queue format in commit ed2ac861f8686c28209bdd50059f617ef9b01515.
   - File updated: docs/chatgpt_status/distance_property_types/queue/distance_property_types_site_check_20260703_0950.task.json.
   - Top-level fields now exist:
     - no_fake_final_ready=true
     - no_db_write=true
     - no_migration=true
     - no_production_deploy=true
     - fake_data=false
     - db_write=false
     - migration=false
     - production_deploy=false
     - final_ready=false

5. But there is no post-fix pickup evidence yet for distance_property_types:
   - Missing: docs/chatgpt_status/distance_property_types/status/distance_property_types_site_check_20260703_0950.status.json
   - Missing: docs/chatgpt_status/distance_property_types/heartbeat/distance_property_types_site_check_20260703_0950.heartbeat.json
   - Missing: docs/chatgpt_status/distance_property_types/runner_outputs/distance_property_types_site_check_20260703_0950.report.json
   - Existing progress report still says final_ready=false and evidence_rows=0.

## Most likely current root cause

The stable runner completed a healthy scan at 2026-07-07T18:25:07Z before the fixed distance_property_types queue was picked up, or the launcher/daemon is not running continuous pickup cycles after the health scan.

The runner is healthy but idle/one-shot. It is not currently producing new per-page pickup artifacts.

## Required Codex fix / action

1. Do not create a new runner.
2. Do not return to old V5 runner.
3. Use only existing launcher:
   C:\Users\cagda\Documents\GitHub\AAYS\START_AAYS_RUNNER.bat
4. Confirm the launcher starts the stable legacy worktree runner continuously, not just one scan.
5. Run/poll the existing stable runner after commit ed2ac861f8686c28209bdd50059f617ef9b01515 is present locally.
6. Confirm queue_selection_debug after the queue fix contains distance_property_types as valid/ready.
7. Produce fresh GitHub evidence after the queue fix:
   - docs/chatgpt_status/_shared/status/stable_runner_daemon_latest.json with checked_at after the queue fix and runner_exit_code=0.
   - docs/chatgpt_status/_shared/reports/MULTI_PAGE_runner_output_<new_run_id>.json showing queue_started=true or an explicit skip/block reason.
   - docs/chatgpt_status/distance_property_types/status/distance_property_types_site_check_20260703_0950.status.json.
   - docs/chatgpt_status/distance_property_types/heartbeat/distance_property_types_site_check_20260703_0950.heartbeat.json.
   - docs/chatgpt_status/distance_property_types/runner_outputs/distance_property_types_site_check_20260703_0950.report.json.
8. If source input rows are missing, do not mark final. Write blocked/completed_no_real_evidence_rows with final_ready=false.

## Acceptance condition

The problem is solved only when GitHub contains fresh post-fix artifacts proving one of these states:

A. distance_property_types was picked up and wrote status/heartbeat/runner_output; or
B. distance_property_types was explicitly blocked/skipped with a page-local reason and final_ready=false.

A healthy shared daemon alone is not enough anymore.

## Do not do

- Do not start parallel runner.
- Do not make F: canonical.
- Do not fake completed.
- Do not fake 100 percent.
- Do not set final_ready=true.
- Do not DB write.
- Do not migrate.
- Do not production deploy.
