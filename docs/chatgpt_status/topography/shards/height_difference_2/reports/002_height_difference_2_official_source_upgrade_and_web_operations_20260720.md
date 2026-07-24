# height_difference_2 — Official Source Upgrade and Row-Level Web Operations

- SLOT_ID: `height_difference_2`
- Parcel partition: `30762-61522` (`30761` rows)
- Branch: `codex/aays-single-runner-v5-20260706`
- Resume checkpoint: `sequence=1`
- Task: `topography-height-difference-2-official-source-upgrade-20260720`
- Batch: `height-difference-2-source-upgrade-20260720T162400Z`
- Checked at: `2026-07-20T16:24:00Z`
- Result: `SOURCE_CONTRACTS_UPGRADED_PARCEL_INPUT_BLOCKED`

## Work completed

Twelve bounded operations were evaluated in three official-source tracks. Ten operations completed and two remained explicitly blocked.

- planned operations: `12`
- completed operations: `10`
- blocked operations: `2`
- batch operation completion: `83.33%`
- overall layer completion: `78%`
- overall increase: `+0%`

The overall layer percentage was not increased because no real parcel in rows `30762-61522` has both canonical geometry and an official numeric sample.

## Upgraded official source contracts

### 1. HM Land Registry INSPIRE Index Polygons

- Role: primary official indicative parcel geometry.
- Current metadata date found: `2026-07-08`.
- Update frequency: monthly.
- Delivery: local-authority GML files.
- CRS: British National Grid, `EPSG:27700`.
- Scope: freehold registered-property subset in England and Wales.
- Boundary meaning: indicative position and extent, not a legal title-plan boundary.
- Accuracy rule: perform parcel matching in EPSG:27700; do not use a WGS84-transformed polygon for the primary match because published technical guidance warns that reprojection may shift some features by up to 15 metres.

### 2. Environment Agency LIDAR Composite DTM 1m

- Role: primary official numeric elevation source.
- Coverage: approximately 99% of England.
- Resolution: 1 metre.
- Delivery: GeoTIFF 5 km tiles and persistent WCS service.
- Height datum: Ordnance Survey Newlyn.
- Horizontal CRS: `EPSG:27700`.
- Published vertical accuracy for component surveys: `+/-0.15 m RMSE`.
- Additional endpoint: official OGC API Features survey-index service for coverage and survey metadata.

### 3. OS Terrain 50

- Role: secondary official numeric cross-check.
- Version: July 2026.
- Coverage: Great Britain.
- Grid spacing: 50 metres.
- Tile size: 10 km.
- Published grid accuracy: 4 m RMSE.
- Licence: Open Government Licence.
- Use restriction in this workflow: independent cross-check only; it does not replace EA DTM 1m as the primary elevation source.

## Locked sampling method

1. Bind `row_no`, `parcel_id`, `hmlr_inspire_id`, `hmlr_lat`, and `hmlr_lon` from the canonical matrix for rows `30762-61522`.
2. Match HMLR INSPIRE GML features in `EPSG:27700`.
3. Sample EA DTM 1m over the real polygon and calculate median plus interquartile range.
4. Do not promote a centroid-only value as a measured parcel result when the polygon is absent.
5. Use OS Terrain 50 as an independent secondary cross-check.
6. Preserve `NO_DATA` when any mandatory evidence gate fails.

## Row-level website publication

A shard-specific page and JSON artifacts were added so the user can inspect each operation separately after the canonical web root syncs:

- page: `england_map_web/data/aays_18_slots/height_difference_2/index.html`
- operations: `england_map_web/data/aays_18_slots/height_difference_2/operations_latest.json`
- status: `england_map_web/data/aays_18_slots/height_difference_2/status_latest.json`

The page displays:

- operation number and status;
- stage and operation type;
- official source name and URL;
- evidence summary;
- accuracy classification;
- exact blocker.

GitHub commits produced in this batch:

- source contracts: `d3fa62d66a80f2d8afb968fbefe97d287bfba18f`
- row-level operations: `a53ae3bc5faa7ce66020693b48f128398ae07808`
- web status: `5154ce16f957ffe9eaf72e40f9d1315f9dedbdb6`
- shard web page: `f5d7c49b66ff3fe0dc2dd27e98517a785bc7c61a`

## Candidate result

- official source candidates established: `3`
- official source contracts upgraded: `3`
- real shard parcel candidates selected: `0`
- measured parcel rows written: `0`
- parcel geometry rows written: `0`
- official numeric rows written: `0`

No synthetic parcel identifiers, coordinates, boundaries, or elevations were created.

## Real blockers

- `CANONICAL_8012_MATRIX_SHARD_EXPORT_REQUIRED`
- `ROW_NO_PARCEL_ID_INSPIRE_ID_LAT_LON_EXPORT_MISSING`
- `REAL_SHARD_PARCEL_BOUNDARY_REQUIRED`
- `EA_DTM_NUMERIC_SAMPLE_REQUIRED`
- `OS_TERRAIN_SECONDARY_CROSSCHECK_REQUIRED`
- `CANONICAL_PORT_8012_HTTP_READBACK_NOT_AVAILABLE_IN_THIS_EXECUTION_ENVIRONMENT`

## Next unverified step

`EXPORT_CANONICAL_SHARD_ROWS_THEN_SELECT_3_REAL_PARCELS_AND_SAMPLE_EA_DTM_1M_WITH_OS_TERRAIN50_CROSSCHECK`

The next batch may promote parcel values only after the canonical matrix export is present and each selected row passes real geometry, primary numeric, and secondary numeric evidence gates.

## Safety state

- `final_ready=false`
- `product_final_ready=false`
- `fake_data=false`
- `db_write=false`
- `migration=false`
- `production_deploy=false`
