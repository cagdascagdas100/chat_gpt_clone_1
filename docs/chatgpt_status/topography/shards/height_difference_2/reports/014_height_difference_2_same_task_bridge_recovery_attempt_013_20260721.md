# height_difference_2 — Same-task bridge recovery, attempt 013

- Slot: `height_difference_2`
- Parcel range: `30762-61522`
- Task: `aays1-height-difference-2-canonical-export-official-sampling-20260720`
- Attempt: `height-difference-2-20260721-013`
- Checkpoint: `13`
- Final ready: `false`

## Work completed

1. Re-read checkpoint 12, slot status, slot heartbeat, main watcher heartbeat and real output paths without replaying terminal work.
2. Confirmed the historical repo-to-bridge watcher still points to `main` and its last remote heartbeat remains `20260703_225536`.
3. Confirmed the authoritative codex branch task cannot safely be exposed by copying only a queue file because the automation and canonical source are not present on `main`.
4. Added `020_prepare_branch_aware_same_task_bridge.py` to reuse the existing source repo, watch worktree, active repo and bridge; it creates no task, runner, worktree or process.
5. Added duplicate detection across all bridge states and Git-blob hash verification for every copied task-declared path.
6. Added `021_verify_three_source_output_promotion.py` to require exactly rows `30762`, `46142`, `61522`, three distinct HMLR identities, three exact polygons, three EA polygon samples, three Terrain50 crosschecks and port 8012 acceptance.
7. Validation passed `34/34` using local positive and negative fixtures. Fixtures were not promoted or committed as product rows.
8. Aligned JSON, portable and legacy views to the same task/idempotency key and attempt 013.
9. Published web operation rows `166-185`; the manifest now expects `185` visible rows.

## Current evidence

- Source contracts upgraded/revalidated: `4`
- Automation tests: `137/137`
- Real candidate rows: `0`
- Exact HMLR polygon rows: `0`
- EA DTM 1m polygon sample rows: `0`
- OS Terrain 50 crosscheck rows: `0`
- Official numeric rows: `0`
- Web operation rows: `185`
- Overall completion: `78%`
- Batch completion: `84.08%` (`169/201`)

## Real blocker

`BRANCH_AWARE_SAME_TASK_BRIDGE_RECOVERY_NOT_YET_APPLIED; EXISTING_SINGLE_SHARED_RUNNER_CLAIM_NOT_OBSERVED; THREE_REAL_CANDIDATE_SEEDS_PENDING; THREE_EXACT_HMLR_POLYGONS_PENDING; THREE_EA_DTM1M_POLYGON_SAMPLES_PENDING; THREE_OS_TERRAIN50_CROSSCHECKS_PENDING; PORT_8012_HTTP_READBACK_PENDING`

The prepared recovery must run on the existing F resources. It does not start a process or runner; it only reuses the existing worktree/bridge and copies the same idempotent task when absent from every bridge state.

Safety remains: `fake_data=false`, `db_write=false`, `migration=false`, `production_deploy=false`, `final_ready=false`.
