# Height Difference 3 — Sequence 22

## Scope
- Slot: `height_difference_3`
- Parcel rows: `61523-92283` (`30,761` rows)
- Existing shared runner only
- No queue, lease, synthetic claim, owner assignment, heartbeat creation, new runner, or parallel runner

## Remote state readback
- Sequence 21 remained authoritative at cycle start.
- Current task remained `idle`, task ID null, owner null.
- Heartbeat remained stale and `unclaimed`.
- Real runtime remained `NOT_STARTED`; all real counters remained zero.

## Gap closed
The previous control audit accepted only the pre-claim idle/unclaimed state. A legitimate shared-runner pickup would change current-task and heartbeat state, causing the audit to block the very execution it was intended to protect.

## Implemented
1. Upgraded `036_audit_existing_runner_control_plane.py` to accept exactly two modes:
   - `PRECLAIM_IDLE_UNCLAIMED`
   - `CLAIMED_RUNNING_COHERENT`
2. Claimed mode requires the task ID and non-empty owner ID to agree across current-task and heartbeat, a non-stale heartbeat timestamp, and an approved active state.
3. Added fail-closed resumable runtime validation: integer non-negative counters, operation-count equality, unique contiguous ordered operation numbers, and approved runtime status families.
4. Added `037_audit_control_then_run_full_pipeline.py`:
   - safe fast-forward via existing `035`;
   - re-executes the freshly synced `037` from the worktree;
   - requires `036`, `037`, and task-contract files to match clean HEAD blobs;
   - runs `036` before `032`;
   - never creates or mutates claim, queue, lease, owner, heartbeat, task, or runner.
5. Updated existing task contract `012` to invoke `037`, not a new task or queue entry.
6. Updated runtime and current-task contracts to expose the audited entrypoint while preserving idle/unclaimed state.

## Validation
- New tests: `24/24 PASS`
- Cumulative tests: `292/292 PASS`
- Fixture values were not published.
- Real source downloads and port 8012 acceptance were not executed in this environment.

## Official sources refreshed
- HM Land Registry INSPIRE publication: 5 July 2026, monthly, GML by local authority, unique Land Registry-INSPIRE ID.
- Environment Agency LIDAR Composite DTM: 1 m, EPSG:27700, persistent WCS, component survey accuracy ±15 cm RMSE.
- OS Terrain 50: July 2026 version, Great Britain coverage, 50 m terrain grid and official open-data supply formats.

## Real evidence counters
- Canonical shard rows exported: `0/30,761`
- Real candidates: `0`
- HMLR matches: `0`
- EA DTM samples: `0`
- Terrain 50 samples: `0`
- Published real website examples: `0`
- Port 8012 accepted: `false`

## Next unverified step
`RUN_037_SAFE_SYNC_REEXEC_CONTROL_AUDIT_THEN_EXISTING_032_FULL_PIPELINE_AND_TRANSACTIONAL_PORT_8012_ACCEPTANCE`

## Blockers
1. Existing F runner has not claimed or manually executed the committed audited task.
2. Three real canonical rows with official HMLR, EA and OS crosschecks are absent.
3. Transactional port 8012 JSON/GeoJSON/runtime readback is absent.

`final_ready=false`, `product_final_ready=false`, `fake_data=false`, `db_write=false`, `migration=false`, `production_deploy=false`.
