# height_difference_2 — Runtime Receipt Attempt 014

- SLOT_ID: `height_difference_2`
- Parcel range: `30762-61522`
- Task: `aays1-height-difference-2-canonical-export-official-sampling-20260720`
- Attempt: `height-difference-2-20260721-014`
- Final ready: `false`

## Work completed

1. Re-read checkpoint 13, slot heartbeat and missing recovery/candidate outputs.
2. Reconfirmed that the existing F bridge recovery had not executed.
3. Found a duplicate-detection defect: the old marker scan depended on the filename containing the full hyphenated task ID, while the queue filename uses underscores.
4. Added JSON-identity bridge marker resolution.
5. Added safe reuse of one existing pending copy of the same task.
6. Added fail-closed blocking for running, done or processed copies and for multiple pending copies.
7. Added runtime-ready receipt writing with SHA256 verification.
8. Added an independent runtime receipt verifier.
9. Added one portable PowerShell entrypoint that runs recovery and receipt verification without starting a process, runner, worktree or new task.
10. Routed the root portable task to the new runtime recovery entrypoint.
11. Validated the new and existing-pending paths plus terminal duplicate blocking: `36/36 PASS`.

## Current result

The same task is ready to run the recovery entrypoint through the existing portable runner. The entrypoint will place or reuse exactly one JSON-identity-matched task in the existing F bridge pending directory and mark only that runtime copy ready for claim.

No real candidate, HMLR polygon, EA DTM 1m sample, OS Terrain 50 crosscheck or port 8012 acceptance output exists yet. No measured parcel value was produced.

## Blocker

`SAME_TASK_RUNTIME_RECOVERY_ENTRY_NOT_YET_EXECUTED_ON_EXISTING_F_PORTABLE_RUNNER; EXISTING_SINGLE_SHARED_RUNNER_CLAIM_NOT_OBSERVED; THREE_REAL_CANDIDATE_SEEDS_PENDING; THREE_EXACT_HMLR_POLYGONS_PENDING; THREE_EA_DTM1M_POLYGON_SAMPLES_PENDING; THREE_OS_TERRAIN50_CROSSCHECKS_PENDING; PORT_8012_HTTP_READBACK_PENDING`

Safety flags remain false for fake data, database writes, migrations and production deployment.
