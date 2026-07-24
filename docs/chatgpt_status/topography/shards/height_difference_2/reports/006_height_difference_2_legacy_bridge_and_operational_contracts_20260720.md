# height_difference_2 — Legacy Pickup Bridge and Operational Source Contracts

- SLOT_ID: `height_difference_2`
- Parcel partition: `30762-61522` (`30761` rows)
- Branch: `codex/aays-single-runner-v5-20260706`
- Task: `aays1-height-difference-2-canonical-export-official-sampling-20260720`
- Checkpoint: `4 -> 5`
- Result: `DUAL_MODE_PENDING_UNCLAIMED`
- Updated: `2026-07-20T23:12:00+03:00`

## Completed work

1. Re-read global current-task, slot heartbeat and expected runner output.
2. Verified heartbeat remains unclaimed and no runner output exists.
3. Read successful historical runner recovery commits and confirmed the legacy runner can require `.queue.txt`, `.current.txt` and `control/current_task.txt` because JSON queue files were not consumed.
4. Created a legacy `STATUS=READY` queue contract for the same task ID.
5. Created the matching legacy per-task current bridge.
6. Repointed the stale control alias to the already-selected height_difference_2 task after confirming no live lease.
7. Updated task, global current-task and slot current-task records to dual pickup mode without creating a duplicate task.
8. Locked a machine-use snapshot for current HMLR INSPIRE, Environment Agency DTM 1 m WCS and OS Terrain 50 contracts.
9. Published operations `40-50` and a 50-row merged web view.

## Progress

- planned operations: `65`
- completed operations: `43`
- blocked operations: `3`
- pending operations: `1`
- batch percent: `66.15%`
- batch increase: `+6.15%`
- overall layer percent: `78%`
- overall increase: `+0%`
- official source candidates: `3`
- upgraded sources: `3`
- operational endpoint contracts locked: `3`
- source contract accuracy: `4.0/4`
- real parcel candidates: `0`
- measured parcel rows: `0`
- visible web operation rows: `50`

## Official operational contracts

1. HMLR INSPIRE: 5 July 2026 release; first-Sunday monthly cycle; one GML file per listed local authority; indicative extent only.
2. Environment Agency DTM 1 m: persistent WCS 2.0.1 raw-pixel route; EPSG:27700; GeoTIFF NoData sentinel `-3.4028235e+38`; CoverageId must be discovered at runtime.
3. OS Terrain 50: July 2026 Great Britain release; multiple open formats; independent coarse crosscheck only.

## Current blocker

`EXISTING_SINGLE_SHARED_RUNNER_CLAIM_PENDING; CANONICAL_MATRIX_SHARD_EXPORT_PENDING; THREE_REAL_HMLR_BOUNDARY_MATCHES_PENDING; THREE_EA_DTM_1M_POLYGON_SAMPLES_PENDING; THREE_OS_TERRAIN50_CROSSCHECKS_PENDING; PORT_8012_HTTP_READBACK_PENDING`

## Next verified step

The existing single shared runner must claim either representation of the same idempotent task. It must export canonical rows `30762-61522` before selecting up to three real parcels. No parcel, coordinate, geometry or elevation may be invented.

## Safety

- `single_runner_only=true`
- `new_runner=false`
- `parallel_runner=false`
- `final_ready=false`
- `fake_data=false`
- `db_write=false`
- `migration=false`
- `production_deploy=false`
