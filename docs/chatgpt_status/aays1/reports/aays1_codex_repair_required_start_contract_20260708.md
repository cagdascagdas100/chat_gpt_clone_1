# aays1 Codex Repair Start Contract - 2026-07-08

PAGE_KEY: aays1
Repo: cagdascagdas100/chat_gpt_clone_1
Branch: codex/aays-single-runner-v5-20260706
User intended local root: C:\AAYS_WT\AAYS_RUNNER_HEALTHY_20260707
Launcher: C:\Users\cagda\Documents\GitHub\AAYS\START_AAYS_RUNNER.bat

## User goal

The runner is only the continuation mechanism. The real goal is to continue the original TerraYield/AAYS plan for this page, make program changes, update the site-visible output, and let the user continue by typing only `devam et`.

## Current GitHub evidence

1. runner_bootstrap_latest.json still shows C:\AAYS_WT\AAYS_RUNNER_CLEAN_20260707, not C:\AAYS_WT\AAYS_RUNNER_HEALTHY_20260707.
2. MULTI_PAGE_latest_status.json shows queue_seen=true but queue_started=false.
3. MULTI_PAGE_latest_status.json shows runner_output_uploaded=false and PUSH_SYNC_OK=false.
4. aays1 queue file normalized_065_progress_report_20260706.json is status=blocked.

## Required missing structures

Codex must repair or add:

1. Fresh shared runner evidence under docs/chatgpt_status/_shared/status, heartbeat, and reports.
2. A valid aays1 queue task under docs/chatgpt_status/aays1/queue with status queued or pending.
3. A real automation script under docs/chatgpt_status/aays1/automation.
4. Fresh aays1 status output under docs/chatgpt_status/aays1/status.
5. Fresh aays1 report output under docs/chatgpt_status/aays1/reports.
6. Fresh aays1 heartbeat under docs/chatgpt_status/aays1/heartbeat.
7. Fresh runner output under docs/chatgpt_status/aays1/runner_outputs or shared reports.
8. Site-visible TerraYield/AAYS program output files, or an exact report of which site paths are missing from this branch.

## Valid aays1 task contract

The new or repaired task must include:

- page_key=aays1
- target_branch=codex/aays-single-runner-v5-20260706
- automation_script under docs/chatgpt_status/aays1/automation
- new_runner_allowed=false
- single_shared_runner_required=true
- allowed_paths limited to docs/chatgpt_status/aays1/
- final_ready=false unless real evidence proves completion
- fake_data=false
- db_write=false
- migration=false
- production_deploy=false

## Acceptance evidence

A valid fix must show in GitHub:

- runner_exit_code=0
- queue_started=true for a valid aays1 task
- runner_output_uploaded=true
- PUSH_SYNC_OK=true
- fresh readable MULTI_PAGE_runner_output JSON
- fresh aays1 status/report/heartbeat output
- program or site-visible files changed if product work is required

## Codex instruction

Do not create another runner. Repair or prove the existing shared stable runner, then queue a real aays1 product/site task or a real pickup probe. If the product/site paths are missing, report the exact missing paths. Do not claim completion until both runner evidence and site-visible output exist.
