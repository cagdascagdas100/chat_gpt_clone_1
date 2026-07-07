# CODEX PRODUCT WORK CLARIFICATION - aays1

PAGE_KEY: aays1
Branch: codex/aays-single-runner-v5-20260706

## Conclusion

The runner is not the product work. The runner has already proven it can pick up and execute a task for aays1. The reason the user cannot observe real TerraYield/AAYS site progress is that the current aays1 product automation is a blocked placeholder.

## Current product blocker

The active aays1 product path is:

- docs/chatgpt_status/aays1/automation/065_parallel_source_evidence_batch.ps1

That script currently writes:

- BLOCKED_SCRIPT_CREATION_REQUIRES_SOURCE_FETCH_IMPLEMENTATION
- AAYS1_065_BLOCKED_REAL_SOURCE_FETCH_IMPLEMENTATION_REQUIRED

Therefore pressing continue only re-runs a safe blocked task. It does not update TerraYield site data or UI-visible outputs.

## What Codex must implement next

Codex should stop treating this as runner repair. It should implement real product work for aays1:

1. Replace the placeholder 065 automation with real source/evidence fetch logic.
2. Produce concrete output under docs/chatgpt_status/aays1/status, reports, heartbeat, and runner_outputs.
3. If the product work changes the visible site, update the appropriate england_map_web data/UI files in the same branch.
4. Keep all safety gates: final_ready=false unless real evidence gates pass; fake_data=false; db_write=false; migration=false; production_deploy=false.
5. Push GitHub evidence so the user can observe the change from the site/repo.

## Acceptance criteria

A valid next result is not another runner smoke test. A valid next result must include:

- real product output or a specific source/evidence blocker,
- updated site-visible files if the task requires UI/site visibility,
- a runner output proving the product task was executed,
- no fake completed state.

## Safety flags

final_ready=false
product_final_ready=false
fake_data=false
db_write=false
migration=false
production_deploy=false
