# height_difference_3 — EA query preparation and single-runner contract

- SLOT_ID: `height_difference_3`
- Parcel range: `61523-92283`
- Previous checkpoint: `3`
- Cycle timestamp: `2026-07-20T19:24:27Z`
- Result: `OFFICIAL_QUERY_PIPELINE_READY; CANONICAL_8012_EXPORT_STILL_BLOCKED`

## Progress completed in this cycle

1. Remote slot checkpoint and idle current-task state were re-read.
2. Environment Agency LIDAR Composite DTM 1m metadata was refreshed from the official publisher.
3. The persistent EA WCS endpoint was recorded.
4. The Defra OGC API Features landing page and collection catalogue were read.
5. The exact collection `LIDAR_Composite_1m_DTM_2022_extents` was resolved.
6. Queryable tile fields were locked: filename, tilename, polygon ID, resolution, year, source DTM filename and survey dates.
7. The official items endpoint was confirmed to return real tile inventory rows.
8. OS Terrain 50 structure and 4 m RMSE documentation were refreshed.
9. HMLR EPSG:27700 processing and 15 m reprojection-warning rules were retained.
10. A machine-readable source and query contract was published.
11. A runnable canonical-export validator and first-three query preparer was published.
12. A seven-step existing-single-runner execution contract was published.
13. Website operation rows were expanded from 16 to 38.

## New executable artifact

`docs/chatgpt_status/topography/shards/height_difference_3/automation/004_prepare_three_real_sample_queries.py`

The program:

- accepts CSV, JSON, JSONL or GeoJSON canonical exports;
- rejects rows outside `61523-92283`;
- rejects duplicate row numbers and unrecorded duplicate parcel IDs;
- requires source-backed WGS84 and British National Grid coordinates;
- requires at least one official parcel identifier;
- selects the first three unresolved rows deterministically;
- queries the official EA tile inventory for each selected coordinate;
- records tile filename, tilename, resolution, year and survey dates;
- parses WCS capabilities and records coverage identifiers or explicit network errors;
- writes no measured height values before the evidence gate passes.

## Official source hierarchy

1. Geometry: HMLR INSPIRE Index Polygons in EPSG:27700.
2. Primary numeric elevation: Environment Agency LIDAR Composite DTM 1 m.
3. Independent numeric crosscheck: OS Terrain 50.
4. Diagnostic only: Copernicus GLO-30.

## Current evidence counts

- official source candidates: `4`
- high-confidence source candidates: `3`
- source/query contracts published: `4`
- website operation rows: `38`
- current-cycle operations processed: `22/22`
- current-cycle completed operations: `17`
- current-cycle blocked operations: `5`
- canonical shard rows exported: `0`
- selected real parcel candidates: `0`
- HMLR boundary matches: `0`
- EA DTM numeric samples: `0`
- OS Terrain 50 crosschecks: `0`
- measured parcel rows written: `0`

## Accuracy

- source hierarchy readiness: `3.9/4`
- query-preparation and input-validation contract: `4/4`
- parcel measurement accuracy: `0/4_NOT_PRODUCED`

The measurement score remains zero because no real shard parcel has yet been bound to canonical coordinates and an official boundary. This is an evidence state, not an estimate of the future method.

## Blocker

`CANONICAL_8012_MATRIX_SHARD_EXPORT_REQUIRED; ROW_NO_PARCEL_ID_OFFICIAL_IDS_COORDINATES_EXPORT_MISSING; REAL_SHARD_PARCEL_BOUNDARY_REQUIRED; EA_DTM_1M_NUMERIC_SAMPLE_REQUIRED; OS_TERRAIN50_INDEPENDENT_CROSSCHECK_REQUIRED`

## Next step

`EXPORT_CANONICAL_SHARD_ROWS_THEN_RUN_004_PREPARE_THREE_REAL_SAMPLE_QUERIES`

After the canonical export is present, the existing single shared runner can immediately select three real records, resolve EA tile metadata, match current HMLR GML, sample EA DTM 1 m and crosscheck OS Terrain 50.

No new runner, parallel runner, inferred coordinate, nearest-point value or measured parcel value was created.

`final_ready=false`, `product_final_ready=false`, `fake_data=false`, `db_write=false`, `migration=false`, `production_deploy=false`.
