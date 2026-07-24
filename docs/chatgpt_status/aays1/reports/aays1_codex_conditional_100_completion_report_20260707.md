# AAYS1 Codex Conditional Completion Report

Repo root: C:\AAYS_WT\AAYS_RUNNER_HEALTHY_20260707
Branch: codex/aays-single-runner-v5-20260706
Page key: aays1
Runner: existing single shared stable runner only
Launcher: C:\Users\cagda\Documents\GitHub\AAYS\START_AAYS_RUNNER.bat

## Current state

Runner pickup is proven. The aays1 pickup probe is done and PUSH_SYNC_OK is true.

The remaining work is not a runner problem. The remaining work is product implementation and site visibility.

## Main problem

The queued product task 091 points to docs/chatgpt_status/aays1/automation/065_parallel_source_evidence_batch.ps1.
That script does not perform real product evidence work. It writes a blocked result saying source/evidence fetch implementation is required.

The site panel also contains stale aays1 status from older evidence and must be updated to show the real current product state instead of stale completion.

## Required Codex work

1. Do not create a new runner.
2. Do not start V5 runner.
3. Use only the existing stable shared runner and the repo root above.
4. Check every queue JSON before parsing. Invalid JSON or conflict markers must be skipped and reported, not allowed to crash the full runner.
5. Make latest shared status files reflect the latest run, not stale 18:25 evidence.
6. Replace or implement the aays1 product automation so it does real source/evidence work instead of only writing the 065 blocker.
7. Update the site-visible data under england_map_web/data/runner_panel/page_status_index.json so the web UI shows the real aays1 status.
8. Keep final_ready false unless real acceptance evidence exists.
9. Keep fake_data=false, db_write=false, migration=false, production_deploy=false.
10. Commit and push all evidence to branch codex/aays-single-runner-v5-20260706.

## Product acceptance conditions

AAYS1 is not complete until GitHub evidence shows all of these:

- stable runner processed the real aays1 product task
- runner_exit_code=0
- queue_started=true
- runner_output_uploaded=true
- PUSH_SYNC_OK=true
- aays1 status/report/heartbeat were written
- site panel JSON was updated and pushed
- no fake completed marker
- no fake 100 percent
- no fake final_ready true
- no DB write
- no migration
- no production deploy

## Expected final files to inspect

- docs/chatgpt_status/_shared/status/stable_runner_daemon_latest.json
- docs/chatgpt_status/_shared/status/MULTI_PAGE_latest_status.json
- docs/chatgpt_status/_shared/status/runner_bootstrap_latest.json
- docs/chatgpt_status/aays1/queue/091_aays1_real_product_evidence_fetch_20260707.task.json
- docs/chatgpt_status/aays1/queue/092_aays1_site_status_sync_20260707.task.json
- docs/chatgpt_status/aays1/status/
- docs/chatgpt_status/aays1/reports/
- docs/chatgpt_status/aays1/heartbeat/
- england_map_web/data/runner_panel/page_status_index.json

## Final rule

If real product evidence is still missing, leave final_ready=false and write a clear blocker. Do not mark done. Do not mark 100 percent. Do not fabricate evidence.
