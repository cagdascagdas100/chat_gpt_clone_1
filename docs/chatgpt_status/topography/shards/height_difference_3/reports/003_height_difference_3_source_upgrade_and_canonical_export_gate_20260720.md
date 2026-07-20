# height_difference_3 — Official Source Upgrade and Canonical Export Gate

- SLOT_ID: `height_difference_3`
- Parcel partition: `61523-92283` (`30761` rows)
- Branch: `codex/aays-single-runner-v5-20260706`
- Remote HEAD read before work: `9a7d452c888313847071dcf34a03dd6371328b7c`
- Task: `height_difference_3-official-source-upgrade-and-canonical-export-contract-20260720`
- Checked at: `2026-07-20T19:05:46Z`
- Result: `SOURCE_CONTRACTS_UPGRADED; CANONICAL SHARD EXPORT STILL REQUIRED`

## Completed work

1. Re-read remote slot state: checkpoint sequence `2`, current task `idle`, no owner.
2. Compared the sibling height shard's official source rules read-only; no sibling shard file was modified.
3. Upgraded the shard source hierarchy:
   - geometry: HM Land Registry INSPIRE GML, native EPSG:27700;
   - primary numeric elevation: Environment Agency LIDAR Composite DTM 1 m;
   - secondary numeric crosscheck: OS Terrain 50;
   - diagnostic only: Copernicus GLO-30 DSM.
4. Verified the Environment Agency DTM contract: approximately 99% England coverage, 1 m resolution, 5 km GeoTIFF tiles, Ordnance Datum Newlyn heights, EPSG:27700 and published input-survey vertical accuracy of +/-0.15 m RMSE.
5. Verified the Defra survey-index OGC API landing service and recorded the official WCS contract.
6. Verified the July 2026 OS Terrain 50 release, 50 m grid, 10 km tiles, annual July update and official 4 m RMSE statement.
7. Verified the 5 July 2026 HMLR INSPIRE publication and monthly local-authority GML workflow.
8. Locked native EPSG:27700 processing because HMLR guidance warns WGS84 conversion can shift some features by up to 15 m.
9. Published an exact canonical export schema for rows `61523-92283`, including official IDs, coordinates, BNG coordinates, local-authority keys and optional geometry.
10. Published a deterministic rule for selecting the first three real unresolved shard rows after export.
11. Published 16 website operation rows and a current web status artifact.

## Source and accuracy summary

- source candidates: `4`
- upgraded official source contracts: `3`
- source-contract readiness: `3.9/4`
- historical layer fallback accuracy: `2.5/4`
- new parcel-measurement accuracy: `0/4_NOT_PRODUCED`

The source score is not a parcel-value score. No parcel measurement was promoted because the canonical shard export is absent.

## Website artifacts

- `england_map_web/data/aays_18_slots/height_difference_3/operations_latest.json`
- `england_map_web/data/aays_18_slots/height_difference_3/status_latest.json`

Operation status:

- planned: `16`
- completed: `14`
- blocked: `2`
- batch operation progress: `87.5%`

## Canonical input gate

Published contract:

`docs/chatgpt_status/topography/shards/height_difference_3/inputs/003_canonical_8012_shard_export_contract_20260720.json`

Required before selecting examples:

- row numbers `61523-92283`;
- `parcel_id` and authoritative parcel identifiers;
- source-backed longitude/latitude and BNG easting/northing;
- local-authority name/code;
- source version and data status;
- official geometry or a documented coordinate binding.

Expected web export paths:

- `canonical_export/manifest.json`
- `canonical_export/filter_indexes.json`
- `canonical_export/pages/page_*.json`

## Blocker

`CANONICAL_8012_MATRIX_SHARD_EXPORT_REQUIRED; ROW_NO_PARCEL_ID_OFFICIAL_IDS_COORDINATES_EXPORT_MISSING; REAL_SHARD_PARCEL_BOUNDARY_REQUIRED; EA_DTM_1M_NUMERIC_SAMPLE_REQUIRED; OS_TERRAIN50_INDEPENDENT_CROSSCHECK_REQUIRED`

## Data-production decision

- parcel candidates selected: `0`
- measured parcel rows written: `0`
- real geometry rows written: `0`
- official numeric rows written: `0`
- inferred or nearest-point rows written: `0`

No existing example outside rows `61523-92283` was promoted into this shard.

## Next unverified step

`EXPORT_CANONICAL_SHARD_ROWS_THEN_SELECT_3_REAL_PARCELS_AND_SAMPLE_EA_DTM_1M_WITH_OS_TERRAIN50_CROSSCHECK`

## Progress

- overall product completion: `78%`
- percentage increase: `0`
- source preparation increased, but product completion did not increase because no parcel-bound numeric evidence passed the gate.

`final_ready=false`, `product_final_ready=false`, `fake_data=false`, `db_write=false`, `migration=false`, `production_deploy=false`.
