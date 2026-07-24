# CODEX RUNNER REPAIR REQUEST - aays1

PAGE_KEY: aays1
Branch: codex/aays-single-runner-v5-20260706
Expected runner: RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_STABLE_20260707

## Current result

Runner is still not verifiable as healthy from GitHub evidence.

## Latest GitHub evidence seen from this page

- runner_bootstrap_latest.json updated_at is still 2026-07-07T09:15:54Z.
- runner_bootstrap_latest.json still reports scan_runner=RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_V5_20260706.
- stable_runner_daemon_latest.json is still old: checked_at=2026-07-07T00:58:43Z.
- stable_runner_daemon_latest.json still reports runner_exit_code=1.
- No post-2026-07-07T15:33:19Z stable daemon status is visible in GitHub from this page.
- No clean stable idle scan or successful aays1 task-processing evidence is visible.

## What Codex must verify/fix locally

1. Ensure only one shared runner process exists.
2. Ensure the active daemon uses RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_STABLE_20260707.ps1, not the V5 scan runner.
3. Ensure bootstrap/status/heartbeat files are pushed to this branch after 2026-07-07T15:33:19Z.
4. Ensure idle scan exits cleanly and writes fresh stable_runner_daemon_latest.json.
5. If a task exists for aays1, write real queue/status/report/heartbeat/runner_outputs/completed-or-blocked evidence.

## Safety

Do not mark completed or final_ready=true from this report.

final_ready=false
product_final_ready=false
fake_data=false
db_write=false
migration=false
production_deploy=false
