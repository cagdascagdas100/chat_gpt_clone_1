# height_difference_2 — V3 Pending Contract and Official Source Refresh

- SLOT_ID: `height_difference_2`
- Parcel partition: `30762-61522` (`30761` rows)
- Branch: `codex/aays-single-runner-v5-20260706`
- Task: `aays1-height-difference-2-canonical-export-official-sampling-20260720`
- Checkpoint: `3 -> 4`
- Updated: `2026-07-20T22:42:00+03:00`
- Result: `V3_PENDING_CONTRACT_PUBLISHED_RUNNER_CLAIM_PENDING`

## Completed work

1. Re-read the remote global task, slot task, heartbeat and expected runner output.
2. Verified that the task remained unclaimed and that no output or heartbeat had been synthesized.
3. Compared the task with a current accepted AAYS 21-slot queue contract.
4. Identified the material pickup mismatch: the accepted contract uses `schema_version=3`, `status=pending`, attempt/idempotency keys, read/write path declarations, resource classes and runtime/publish gates.
5. Added a direct Python runner entrypoint under `docs/chatgpt_status/aays1/automation`.
6. Converted the same task identity to the accepted v3 pending contract; no duplicate task or runner was created.
7. Updated global and slot current-task state to `pending`.
8. Revalidated current official routes for the 5 July 2026 HMLR INSPIRE release, persistent Environment Agency DTM 1 m WCS and July 2026 OS Terrain 50.
9. Published a merged 39-row web operations view.

## Progress

- planned operations: `55`
- completed operations: `33`
- blocked operations: `3`
- pending operations: `1`
- preparation/pickup batch: `60.0%`
- overall layer: `78%`
- increase: `0%`
- official source candidates: `3`
- upgraded source contracts: `3`
- source freshness revalidated: `3`
- real parcel candidates: `0`
- measured parcel rows: `0`
- visible web operation rows: `39`
- source readiness accuracy: `3.9/4`
- layer measurement accuracy: `2.5/4 fallback`
- parcel measurement accuracy: `0/4 not produced`

## Current official source state

1. HM Land Registry INSPIRE Index Polygons: official download page publishes the 5 July 2026 monthly local-authority GML release.
2. Environment Agency LIDAR Composite DTM 1 m: persistent official WCS route retained as the primary numeric elevation source.
3. OS Terrain 50: official OS Data Hub lists the July 2026 Great Britain OpenData version.

## Current blocker

`EXISTING_SINGLE_SHARED_RUNNER_CLAIM_PENDING; CANONICAL_MATRIX_SHARD_EXPORT_PENDING; THREE_REAL_HMLR_BOUNDARY_MATCHES_PENDING; THREE_EA_DTM_1M_POLYGON_SAMPLES_PENDING; THREE_OS_TERRAIN50_CROSSCHECKS_PENDING; PORT_8012_HTTP_READBACK_PENDING`

## Next verified step

The existing shared runner must claim the corrected v3 pending task. It must export canonical rows `30762-61522` before selecting up to three real parcels and attempting official measurements.

## Safety

- `single_runner_only=true`
- `new_runner=false`
- `parallel_runner=false`
- `final_ready=false`
- `fake_data=false`
- `db_write=false`
- `migration=false`
- `production_deploy=false`
