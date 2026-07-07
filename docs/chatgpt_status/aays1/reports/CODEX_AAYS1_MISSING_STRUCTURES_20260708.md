# CODEX AAYS1 MISSING STRUCTURES

PAGE_KEY: aays1
Branch: codex/aays-single-runner-v5-20260706

## User goal

The user wants this page to continue the original AAYS/TerraYield plan with only `devam et`, and to see real progress in the repo/site.

## Current status

Runner pickup is proven at task level. The aays1 smoke task completed with queue_started=true, allowed_paths_enforced=true, runner_output_uploaded=true, post_sync_ok=true, PUSH_SYNC_OK=true, and no blockers.

The remaining blocker is not runner health. The current product script is still a placeholder:

- docs/chatgpt_status/aays1/automation/065_parallel_source_evidence_batch.ps1

It returns:

- BLOCKED_SCRIPT_CREATION_REQUIRES_SOURCE_FETCH_IMPLEMENTATION
- AAYS1_065_BLOCKED_REAL_SOURCE_FETCH_IMPLEMENTATION_REQUIRED

So `devam et` can run the runner, but it cannot complete the original product/site work yet.

## Missing items

Codex must add or repair these items for aays1:

1. A current task definition under docs/chatgpt_status/aays1/current_task/ with task goal, acceptance criteria, required outputs, site-visible outputs, allowed paths, and safety flags.
2. A real aays1 product automation script that performs the requested product work or writes a precise evidence blocker.
3. A valid product queue task under docs/chatgpt_status/aays1/queue/ pointing to that real automation.
4. Output evidence under docs/chatgpt_status/aays1/status, reports, heartbeat, and runner_outputs.
5. If the work must be visible on the TerraYield/AAYS site, the relevant england_map_web data/UI files must be updated and pushed.

## Next Codex action

Do not restart or replace the runner as the main fix. Keep the single stable runner. Implement the missing product layer for aays1, then queue it for the existing runner.

If the original product plan is not available in the repo, write a blocker report naming the missing plan file and exact expected path.

## Safety

final_ready=false
product_final_ready=false
fake_data=false
db_write=false
migration=false
production_deploy=false
