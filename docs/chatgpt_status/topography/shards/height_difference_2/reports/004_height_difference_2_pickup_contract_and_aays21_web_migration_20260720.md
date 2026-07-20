# height_difference_2 — Pickup Contract Repair and AAYS 21 Web Migration

- SLOT_ID: `height_difference_2`
- Parcel partition: `30762-61522`
- Branch: `codex/aays-single-runner-v5-20260706`
- Task: `aays1-height-difference-2-canonical-export-official-sampling-20260720`
- Checkpoint: `2 -> 3`
- Updated: `2026-07-20T22:23:00+03:00`
- Result: `QUEUED_UNCLAIMED_AFTER_COMPATIBILITY_REPAIR`

## Completed work

1. Re-read branch HEAD, global current task, slot current task and slot heartbeat.
2. Verified the same task remains selected and no duplicate task exists.
3. Identified legacy `slots_18` / `aays_18_slots` paths inside an authoritative 21-slot shard.
4. Migrated queue, slot and web output contracts to `slots_21` / `aays_21_slots`.
5. Added non-destructive runner pickup aliases for script, output, report and claim readiness.
6. Added wrapper post-run synchronization from the legacy shard web folder to canonical `aays_21_slots`.
7. Published 29 row-level web operations and an explicit empty candidate artifact.
8. Preserved real heartbeat ownership; no claim, heartbeat, parcel, geometry or elevation was synthesized.

## Progress

- planned operations: `45`
- completed operations: `25`
- blocked operations: `3`
- queued operations: `1`
- preparation/pickup batch: `55.56%`
- overall layer: `78%`
- increase: `0%`
- official source candidates: `3`
- upgraded source contracts: `3`
- real parcel candidates: `0`
- measured parcel rows: `0`
- web operation rows: `29`
- source readiness accuracy: `3.8/4`
- layer measurement accuracy: `2.5/4 fallback`

## Current blocker

`EXISTING_SINGLE_SHARED_RUNNER_UNCLAIMED; CANONICAL_MATRIX_SHARD_EXPORT_PENDING; THREE_REAL_HMLR_BOUNDARY_MATCHES_PENDING; THREE_EA_DTM_1M_POLYGON_SAMPLES_PENDING; THREE_OS_TERRAIN50_CROSSCHECKS_PENDING; PORT_8012_HTTP_READBACK_PENDING`

## Next verified step

The existing shared runner must claim this same task. It must export canonical shard rows before selecting up to three real parcels and attempting official measurements.

## Safety

- `single_runner_only=true`
- `new_runner=false`
- `parallel_runner=false`
- `final_ready=false`
- `fake_data=false`
- `db_write=false`
- `migration=false`
- `production_deploy=false`
