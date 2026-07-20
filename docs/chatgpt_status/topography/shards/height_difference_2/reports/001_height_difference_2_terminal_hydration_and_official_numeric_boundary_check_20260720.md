# height_difference_2 — Terminal Hydration and Real Boundary / Official Numeric Elevation Check

- SLOT_ID: `height_difference_2`
- Parcel partition: `30762-61522` (`30761` rows)
- Branch: `codex/aays-single-runner-v5-20260706`
- Remote HEAD read before work: `d6ff114897969d1763ad32c22529a6d7628d0a83`
- Task: `topography-height-difference-2-hydrate-terminal-159-164-165-real-boundary-official-numeric-elevation-20260720`
- Checked at: `2026-07-20T15:32:15Z`
- Result: `BLOCKED_REAL_BOUNDARY_AND_OFFICIAL_NUMERIC_ELEVATION_EVIDENCE_ABSENT`

## Slot readback

The remote `slots_21/height_difference_2` state was re-read at branch HEAD before any write:

- `status_latest.json`: `state=ready_for_claim`, no owner, no active task.
- `current_task_latest.json`: `state=idle`, `task_id=null`.
- `checkpoint_latest.json`: `sequence=0`.

No other shard was claimed or modified by this task.

## Terminal hydration

The following topography tasks were hydrated from remote GitHub evidence and retained as no-replay history:

1. `159` — `aays1-159-topography-official-source-acceleration-bridge-20260711`
   - remote queue status is `blocked`;
   - automation exit code is `1`;
   - the available extended-consensus snapshot contains three point-coordinate SRTM/ASTER fallback samples;
   - it does not provide real parcel boundaries or official EA LiDAR / OS Terrain parcel sampling;
   - `final_ready=false`.

2. `164` — `aays1-164-topography-public-copdem-cog-sampling-20260713`
   - all `12/12` processing stages are recorded;
   - three CopDEM GLO-30 point samples and three GLO-90 validation samples are present;
   - accuracy remains `2.5/4 fallback`;
   - every candidate row has `boundary_status=pending_real_boundary` and `real_boundary_validated=false`;
   - blockers remain `real_parcel_boundary_required` and `ea_lidar_or_os_terrain_numeric_validation_required`;
   - `final_ready=false`.

3. `165` — `aays1-165-topography-official-lidar-boundary-validation-20260713`
   - all `14/14` processing stages are recorded;
   - four official sources were checked and three were reachable;
   - local official evidence files: `0`;
   - official downloads: `0`;
   - official raster candidates: `0`;
   - EA LiDAR sample rows: `0`;
   - OS Terrain sample rows: `0`;
   - HMLR boundary matches: `0`;
   - completion remains `78%` with `+0` increase and accuracy `2.5/4 fallback`;
   - `final_ready=false`.

## Real geometry and official numeric elevation evidence check

The current canonical validation evidence establishes:

- candidate rows: `3` historical point-sample candidates;
- downloaded official files: `0`;
- local official files: `0`;
- EA LiDAR numeric sample rows: `0`;
- OS Terrain numeric sample rows: `0`;
- official numeric sample rows: `0`;
- HMLR real-boundary match rows: `0`;
- cross-source official validation rows: `0`.

The three historical CopDEM rows are point-based fallback evidence outside this shard-production gate. They are not a real-boundary measurement set and were not expanded, copied, interpolated, or promoted into parcel rows `30762-61522`.

## Data-production decision

No measured, sampled, interpolated, inferred, or proxy parcel elevation or height-difference value was produced for parcel rows `30762-61522`.

- measured parcel rows written: `0`
- parcel geometry rows written: `0`
- official numeric elevation rows written: `0`
- web publication rows written by this shard: `0`
- data-layer files changed by this shard: `0`

## Blocker

`REAL_PARCEL_BOUNDARY_FILE_ABSENT; HMLR_BOUNDARY_MATCH_ROWS_ZERO; EA_LIDAR_SAMPLE_ROWS_ZERO; OS_TERRAIN_SAMPLE_ROWS_ZERO; OFFICIAL_NUMERIC_SAMPLE_ROWS_ZERO; SECOND_OFFICIAL_NUMERIC_SOURCE_ABSENT`

## Next unverified step

`ACQUIRE_REAL_BOUNDARY_AND_OFFICIAL_NUMERIC_ELEVATION_THEN_SAMPLE_ONLY_SHARD_30762_61522`

Required before any parcel value can be published:

1. obtain a real parcel boundary file covering this shard and bind canonical parcel identifiers to geometry;
2. obtain an official numeric elevation raster or point source, such as EA LiDAR or OS Terrain;
3. sample the official source against the real parcel geometry;
4. retain `NO_DATA` for parcels without evidence;
5. validate with a second official numeric source before measured publication.

## Safety state

- `final_ready=false`
- `product_final_ready=false`
- `fake_data=false`
- `db_write=false`
- `migration=false`
- `production_deploy=false`
