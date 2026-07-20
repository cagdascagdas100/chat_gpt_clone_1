# height_difference_1 — Official Source Upgrade Candidate Batch

- SLOT_ID: `height_difference_1`
- Parcel partition: `1-30761`
- Task: `aays1-height-difference-1-official-source-upgrade-candidates-20260720`
- Generated: `2026-07-20T16:21:07Z`
- Web artifact: `england_map_web/data/aays_21_slots/height_difference_1/official_source_candidates_latest.json`

## Result

The terminal hydration from tasks 159, 164 and 165 was retained. Internet research then upgraded the source plan for the three existing candidates without publishing unsupported parcel measurements.

### Official source upgrades

1. HM Land Registry current INSPIRE download page, published 5 July 2026.
2. London Borough of Barnet GML search scope.
3. London Borough of Enfield GML search scope, retained because the candidate corridor is close to the authority boundary.
4. Environment Agency 1 m DTM WCS as the primary official numeric elevation source.
5. Environment Agency 2 m DTM WCS as a same-provider resolution cross-check only.
6. Ordnance Survey Terrain 50 July 2026 release as an independent, lower-resolution secondary numeric source.

## Candidate rows

| parcel_id | parcel_ref | WGS84 | EPSG:27700 | tile | state |
|---|---:|---|---|---|---|
| parcel_2759 | 52040420 | 51.6169525, -0.1430858 | 528658.656, 192535.809 | TQ2892 | source candidates ready; no official numeric value |
| parcel_2758 | 52213916 | 51.6168592, -0.1417993 | 528747.982, 192527.698 | TQ2892 | source candidates ready; no official numeric value |
| parcel_2757 | 52213412 | 51.6167362, -0.1421556 | 528723.664, 192513.392 | TQ2892 | source candidates ready; no official numeric value |

## Progress accounting

- Planned batch operations: `18`
- Completed operations: `13`
- Blocked operations: `5`
- Batch completion: `72.22%`
- Product completion retained from the last verified task-165 state: `78%`
- Product percentage increase: `0%`
- Source upgrades: `6`
- Candidate rows prepared: `3`
- Official measured candidate rows: `0`
- Accuracy remains: `2.5/4 fallback`

No product percentage or parcel accuracy was increased because the official geometry and numeric bytes were not retrieved.

## Real blockers

- `HMLR_BARNET_ENFIELD_GML_BYTES_NOT_FETCHED`
- `EA_LIDAR_1M_WCS_NUMERIC_PIXELS_NOT_FETCHED`
- `OS_TERRAIN50_NUMERIC_GRID_NOT_FETCHED`
- `REAL_BOUNDARY_MATCH_ROWS_0`
- `OFFICIAL_TWO_SOURCE_NUMERIC_VALIDATION_ROWS_0`

## Next verified step

`FETCH_HMLR_BARNET_ENFIELD_GML_THEN_MATCH_3_POINTS_AND_SAMPLE_EA_1M_PLUS_OS_TERRAIN50`

## Safety

- `measured_parcel_values_written=0`
- `output_semantics=NO_DATA_NOT_INFERRED`
- `final_ready=false`
- `product_final_ready=false`
- `fake_data=false`
- `db_write=false`
- `migration=false`
- `production_deploy=false`
