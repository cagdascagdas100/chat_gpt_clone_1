# height_difference_3 — Canonical Security Source Resolved

## Scope

- SLOT_ID: `height_difference_3`
- Parcel rows: `61523-92283`
- Expected shard rows: `30761`
- Canonical rows: `92283`
- `final_ready=false`

## Remote readback

The uploaded local kickoff record was treated as historical only. Remote branch HEAD was re-read as `993690187d9a0cd71c20a57c2857b2b4b0d76da6`. Remote checkpoint sequence is `8`; heartbeat is `unclaimed`; owner and current task are null.

## First unverified step progress

The previously declared source JSONL from `england_map_web/data/program_layer_matrix/manifest.json` is not committed at its declared path. The canonical data is nevertheless available in the committed file:

`england_map_web/data/program_layer_matrix/security.geojson`

Remote and historical validation evidence establishes:

- Blob SHA: `8afd1d2bac414cf0f6b9484014e7878a4ceff877`
- File size: `61,369,763` bytes
- Feature count: `92,283`
- Explicit identity fields: `row_no`, `parcel_id`, `hmlr_inspire_id`
- Source-backed point fields: `hmlr_lon`, `hmlr_lat`, `geometry.coordinates`
- Authority field: `london_authority`

This changes the blocker from unknown/missing canonical source to unexecuted shard extraction.

## New automation

`automation/019_extract_canonical_shard_from_security_geojson.py`

The script fails closed unless all of the following are true:

1. Exactly `92,283` features exist.
2. Explicit `row_no` values are exactly `1-92283`.
3. `parcel_id` and `hmlr_inspire_id` are non-empty and unique.
4. HMLR coordinate fields equal the Point geometry.
5. EPSG:27700 coordinates are derived only through a documented pyproj CRS transformation.
6. Exactly `30,761` explicit rows in `61523-92283` are exported.
7. Existing automation `004` selects the first three unresolved source-backed rows.

No feature order is used as row identity. No nearest-fill logic is enabled.

## Validation

- New tests: `8/8 PASS`
- Cumulative tests: `39/39 PASS`
- Automation accuracy: `4/4`
- Real shard export executed: `no`
- Real candidates selected: `0`
- Real measured rows: `0`
- Real website examples: `0`

## Current blocker

`F_RUNNER_MUST_EXECUTE_019_AGAINST_COMMITTED_SECURITY_GEOJSON; OS_TERRAIN50_LIVE_DOWNLOAD_URL_OR_ARCHIVE_REQUIRED; OFFICIAL_CROSSCHECKED_REAL_ROWS_REQUIRED`

## Next step

`RUN_019_EXTRACT_CANONICAL_SHARD_FROM_SECURITY_GEOJSON_THEN_RUN_004_AND_015`

Safety flags remain false: `fake_data`, `db_write`, `migration`, `production_deploy`.
