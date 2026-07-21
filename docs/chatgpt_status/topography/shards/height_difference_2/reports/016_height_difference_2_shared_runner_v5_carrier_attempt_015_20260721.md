# height_difference_2 — shared runner v5 carrier — attempt 015

- Slot: `height_difference_2`
- Parcel range: `30762-61522`
- Task ID preserved: `aays1-height-difference-2-canonical-export-official-sampling-20260720`
- Idempotency key preserved: `height-difference-2-canonical-export-official-sampling-v3`
- Branch: `codex/aays-single-runner-v5-20260706`
- `final_ready=false`

## Completed

1. Re-read checkpoint 14, slot heartbeat and absent runtime/candidate outputs.
2. Inspected the recent proven shared-runner PowerShell carrier contract.
3. Identified three active-contract mismatches: schema v3 instead of v5, priority 6800 instead of a low numeric priority, and obsolete legacy bridge paths.
4. Added `025_height_difference_2_shared_runner_carrier.ps1`.
5. The carrier resolves the portable repo root, requires the exact codex branch, verifies canonical blob `ca95400a...`, resolves Python and directly runs the existing fail-closed measurement entrypoint.
6. Upgraded the same queue task to schema v5, `pickup_requested`, priority 2, explicit `allowed_paths` and PowerShell execution.
7. Aligned queue current, slot current, portable `ai-tasks/current-task.json`, legacy queue and legacy current-task views.
8. Passed 20/20 deterministic carrier and queue assertions.
9. Published website operation rows 206-225; expected visible rows are now 225.

## Accuracy and safety

- Source-contract accuracy: `4.0/4`
- Automation validation: `193/193 PASS`
- Candidate rows written: `0`
- Exact HMLR polygons written: `0`
- EA DTM 1m polygon samples written: `0`
- OS Terrain 50 crosschecks written: `0`
- Official numeric rows written: `0`
- No legacy point elevation was promoted.
- No new task, runner or parallel runner was created.
- `fake_data=false`, `db_write=false`, `migration=false`, `production_deploy=false`.

## Current blocker

The existing TerraYield portable single shared runner has not yet claimed attempt 015. The task contract is now directly compatible and `ready_for_claim=true`; real candidate and measurement counts remain zero until remote runner output exists.
