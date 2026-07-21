# future_growth_1 — Official Geometry Pipeline Wave 2

## Scope

- Slot: `future_growth_1`
- Parcel rows: `1-30761`
- Canonical rows: `92283`
- Calculation version: `future_growth_v1`
- `final_ready=false`
- `actual_business_data_rows_written=0`

## Continued first unverified step

Wave 1 established six official point candidates for the first three canonical parcels. Wave 2 continues from the missing polygon requirement. It does not repeat the point candidate work and does not claim a Future Growth score.

## Source upgrades

Two additional official geometry source contracts were validated:

1. Greater London Authority Brownfield Register polygon layer
   - official layer: `planning_data_map_02/MapServer/101`
   - geometry: polygon
   - query and GeoJSON contracts available
   - indicative boundary caveat retained
2. HM Land Registry INSPIRE polygons
   - official local-authority download index
   - monthly GML source
   - exact HMLR INSPIRE ID match required for rows 1-3

Official source validation is now `7/16 = 43.75%`, an increase of `12.5` percentage points from wave 1. This is source-contract readiness, not completed data ingestion.

## Automation

Published:

`docs/chatgpt_status/aays1/shards/future_growth_1/automation/002_fetch_official_geometry_and_build_sample_matrix.py`

GitHub blob SHA:

`950c9aeed3047887d17c758d9edcafcc8d3aece9`

The automation fails closed unless the canonical source has exactly 92,283 explicit rows and the first three HMLR INSPIRE IDs remain `39729785`, `39724273`, and `60116682`. It validates official GLA polygons, can parse current HMLR GML polygons, transforms EPSG:4326 geometry to EPSG:27700, and classifies official polygon relations as intersection or bounded proximity. It never emits a Future Growth score before the complete factor matrix is validated.

## Validation

- Relation and source guards: `7/7 PASS`
- Network used by self-test: `no`
- Fake business data written: `no`
- Official GLA polygon payload downloaded: `no`
- Current HMLR GML downloaded: `no`
- Exact parcel polygons extracted: `0/3`
- Verified polygon relations: `0`
- Scored business rows: `0`

## Website outputs

- `england_map_web/data/aays_21_slots/future_growth_1/geometry_acquisition_latest.json`
- `england_map_web/data/aays_21_slots/future_growth_1/geometry_wave_2.html`
- `england_map_web/data/aays_21_slots/future_growth_1/index.html`

The geometry page exposes operations, quality gates and blockers line by line.

## Next unverified step

`EXECUTE_GLA_POLYGON_FETCH_AND_CURRENT_HMLR_GML_EXACT_MATCH_THEN_BUILD_30761_MATRIX`

## Blockers

- `GLA_BROWNFIELD_POLYGON_PAYLOAD_NOT_EXECUTED_BY_NETWORKED_RUNNER`
- `CURRENT_HMLR_BARKING_DAGENHAM_GML_NOT_DOWNLOADED`
- `FULL_30761_ROW_FACTOR_MATRIX_NOT_BUILT`
- `NON_PLANNING_FACTOR_LOADERS_NOT_EXECUTED`

Safety flags remain false: `fake_data`, `db_write`, `migration`, `production_deploy`. “Kesin fiyat tahmini değildir.”
