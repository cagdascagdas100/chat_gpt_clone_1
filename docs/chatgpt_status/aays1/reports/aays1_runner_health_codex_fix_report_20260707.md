# aays1 runner health report for Codex

Repo branch: codex/aays-single-runner-v5-20260706
Page key: aays1

## GitHub evidence

Bootstrap evidence:
- docs/chatgpt_status/_shared/status/runner_bootstrap_latest.json
- runner_status=runner_started
- runner_lock_active=true
- runner_pid=16036
- scan_runner currently reports RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_V5_20260706

Daemon evidence:
- docs/chatgpt_status/_shared/status/stable_runner_daemon_latest.json
- status=runner_loop_completed
- runner_exit_code=1
- CONTINUE_RUNNER_READY=true

Runner report evidence:
- docs/chatgpt_status/_shared/reports/MULTI_PAGE_runner_output_20260707_035718.json
- queue_seen=true
- queue_started=true
- single_runner_lock_acquired=true
- allowed_paths_enforced=false
- runner_output_uploaded=false
- post_sync_ok=false
- PUSH_SYNC_OK=false
- blockers include CONTROLLER_DIRTY_SYNC_SKIPPED and RUNNER_TASK_FAILED

AAYS1 task evidence:
- task_id=normalized-065-progress-report-20260706
- completed=false
- final_ready=false
- observed error includes BLOCKED_UNSCOPED_CHANGES or BLOCKED_WORKTREE_DIRTY for existing aays1 queue, heartbeat, report and status outputs.

## Diagnosis

The runner is being triggered and writes GitHub evidence, but the latest loop is not healthy because it exits with code 1 and fails upload/sync/push. The dirty controller/worktree gate is treating existing runtime or page outputs as blockers. Bootstrap also reports the older V5 scan runner name instead of the expected stable runner name, so the launcher/bootstrap wiring should be checked.

## Fix targets for Codex

1. Align the launcher/bootstrap report with the intended stable single-runner contract.
2. Fix dirty-path classification so expected shared runtime outputs and expected page-key outputs do not permanently block the runner.
3. Enforce allowed_paths while preserving a separate allowlist for shared runner status, heartbeat, lock, log and panel outputs.
4. Fix the git sync step so successful runner loops can produce runner_output_uploaded=true, post_sync_ok=true and PUSH_SYNC_OK=true.
5. Keep normalized-065 non-final unless real evidence exists. If obsolete, mark blocked or skipped_obsolete, not completed.

## Safety

completed=false
final_ready=false
product_final_ready=false
fake_data=false
db_write=false
migration=false
production_deploy=false
