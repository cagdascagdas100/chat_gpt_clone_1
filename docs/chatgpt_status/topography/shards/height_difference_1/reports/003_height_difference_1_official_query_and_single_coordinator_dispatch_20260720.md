# height_difference_1 — Official Query and Single-Coordinator Dispatch

- SLOT_ID: `height_difference_1`
- Parcel partition: `1-30761`
- Task: `height-difference-1-official-boundary-elevation-samples-20260720`
- Remote branch: `codex/aays-single-runner-v5-20260706`
- Remote HEAD before queue creation: `0913cbc7bcf5054dc7adb254f053e544fb1a65c8`
- Updated at: `2026-07-20T19:15:11Z`

## Progress

The existing three candidates were retained without promoting fallback values:

- `parcel_2759` / parcel ref `52040420`
- `parcel_2758` / parcel ref `52213916`
- `parcel_2757` / parcel ref `52213412`

The following new work was completed:

1. Corrected official point-query manifest created for all three candidates.
2. Current HMLR monthly INSPIRE GML contract rechecked for Barnet and Enfield.
3. HMLR WMS `GetFeatureInfo` point queries built in EPSG:27700.
4. EA LiDAR DTM 1 m and 2 m WCS execution contract built.
5. OS Terrain 50 retained as the independent official numeric source.
6. A real-geometry and official-numeric sampling payload was built and syntax checked.
7. A shard-isolated runner wrapper was added.
8. One `.v3.task.json` task was queued for the existing single coordinator.
9. Website operation rows were updated through operation 24.

## Dispatch paths

- Queue: `docs/chatgpt_status/topography/queue/height_difference_1_004_official_boundary_numeric_samples_20260720.v3.task.json`
- Wrapper: `docs/chatgpt_status/topography/shards/height_difference_1/automation/004_official_boundary_numeric_samples_runner_20260720.py`
- Payload: `docs/chatgpt_status/topography/shards/height_difference_1/automation/004_official_boundary_numeric_samples_payload_20260720.b64`
- Query manifest: `docs/chatgpt_status/topography/shards/height_difference_1/source_queries/003_official_point_query_manifest_20260720.md`
- Website rows: `england_map_web/data/aays_21_slots/height_difference_1/official_source_candidates_latest.json`

## Current metrics

- Planned operations: `24`
- Completed operations: `19`
- Blocked operations awaiting real evidence: `5`
- Batch progress: `79.17%`
- Product completion: `78%`
- Product percentage increase: `0%`
- Source upgrades: `9` total, `3` added in this run
- Candidate rows: `3`
- Real boundary matches: `0`
- Official measured rows: `0`
- Current accuracy: `2.5/4 fallback`

## Acceptance guard

The queued payload may publish a measured row only when the candidate point is bound to an actual HMLR polygon and an official EA numeric terrain value is sampled. EA 1 m versus EA 2 m is treated only as a same-provider resolution check. It is not accepted as an independent second source. OS Terrain 50 remains required for independent two-source validation.

No fallback value was promoted, copied, or relabelled as a measured parcel result.

## Current blocker

`SINGLE_COORDINATOR_REMOTE_RESULT_NOT_YET_PRESENT; REAL_BOUNDARY_MATCH_ROWS=0; EA_LIDAR_OFFICIAL_NUMERIC_ROWS=0; OS_TERRAIN50_INDEPENDENT_NUMERIC_ROWS=0`

The authoritative shared-runner heartbeat and claim files currently visible on the branch are historical, so this report records only a successful queue dispatch—not execution or completion.

## Safety

- `final_ready=false`
- `product_final_ready=false`
- `fake_data=false`
- `db_write=false`
- `migration=false`
- `production_deploy=false`
