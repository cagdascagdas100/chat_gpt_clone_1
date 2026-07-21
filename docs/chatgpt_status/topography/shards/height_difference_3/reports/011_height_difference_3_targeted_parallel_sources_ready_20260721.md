# height_difference_3 — Targeted Terrain50 and bounded parallel source readiness

## Scope

- Slot: `height_difference_3`
- Rows: `61523-92283`
- Expected shard count: `30,761`
- Canonical carrier: `england_map_web/data/program_layer_matrix/security.geojson`
- Canonical carrier feature count: `92,283`
- `final_ready=false`

## Work completed

1. Re-read remote branch state, checkpoint sequence 10, status and stale/unclaimed heartbeat.
2. Confirmed there is no real `022` execution output and did not fabricate a lease, heartbeat or completed run.
3. Replaced full-GB Terrain50 acquisition as the preferred path with exact candidate-required 100 km grid-area acquisition.
4. Added `023_download_os_terrain50_required_areas.py`.
5. Added `024_execute_parallel_targeted_sources.py`.
6. Bound HMLR and OS downloads into one bounded parallel group inside the same runner process.
7. Bound EA WCS retrieval and exact Terrain50 tile extraction into a second bounded parallel group.
8. Added official API metadata, MD5, SHA-256, safe ZIP, grid area, grid dimensions, cell size, GML and PRJ gates.
9. Passed 16 of 16 local fail-closed tests. Test fixtures and test values were not committed or promoted.

## Official-source basis

- OS Downloads API exposes product download records including URL, file name, area, format, subformat and optional MD5.
- OpenData download automation can call the official downloads endpoint without a guessed static archive URL.
- Terrain50 supplies 2,858 10 km tiles arranged in 55 100 km grid folders and is refreshed annually in July.
- Terrain50 ASCII tiles are 200 by 200 cells at 50 metre spacing.
- HMLR current INSPIRE files were published on 5 July 2026 and are available by local authority.
- Environment Agency Composite DTM provides approximately 99 percent England coverage at 1 metre resolution in EPSG:27700.

## Runtime reduction

The earlier preferred path downloaded the approximately 157 MB compressed national Terrain50 grid supply. The new preferred path computes the exact OS 100 km grid areas from the first three source-backed BNG coordinates and downloads only those area archives. No neighbouring area is accepted.

Within the existing single runner process:

- HMLR GML acquisition and targeted Terrain50 acquisition may execute concurrently.
- After exact HMLR matching, EA WCS acquisition and exact Terrain50 tile extraction may execute concurrently.
- Maximum concurrent network stages remain two.
- No additional runner, queue item or lease is created.

## Test result

- New tests: `16/16 PASS`
- Cumulative tests: `72/72 PASS`
- Automation validation: `4/4`
- Real targeted downloads: `0`
- Real canonical shard rows exported: `0`
- Real candidates: `0`
- Real official measurement rows: `0`
- Real verified website examples: `0`

## First unverified step

`RUN_024_TARGETED_PARALLEL_HMLR_OS_THEN_EA_TERRAIN50_MEASURE_AND_PUBLISH`

## Blockers

1. The existing F portable runner must execute `024` against the committed canonical `security.geojson`.
2. Official HMLR, OS Downloads API and Environment Agency network calls must complete on that runner.
3. Current HMLR polygon, EA DTM numeric sample and Terrain50 exact tile cross-check must pass before any value is published.

## Safety

- `final_ready=false`
- `product_final_ready=false`
- `fake_data=false`
- `db_write=false`
- `migration=false`
- `production_deploy=false`
- no new runner
- no parallel runner
- no queue submission
