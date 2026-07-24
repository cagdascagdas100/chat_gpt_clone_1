# height_difference_2 — exact HMLR polygon gate / attempt 009

- Slot: `height_difference_2`
- Parcel range: `30762-61522`
- Existing task ID: `aays1-height-difference-2-canonical-export-official-sampling-20260720`
- Attempt: `height-difference-2-20260721-009`
- New or parallel runner: `false`
- Final ready: `false`

## Work completed

1. Reread checkpoint 8, heartbeat and expected outputs without replaying completed work.
2. Revalidated the July 2026 official HMLR INSPIRE, Environment Agency DTM 1m and OS Terrain 50 contracts.
3. Identified and closed the candidate-seed to HMLR starter-manifest schema gap.
4. Added strict EPSG:4326 to EPSG:27700 candidate conversion.
5. Added current HMLR authority-link resolution and safe GML/XML download preparation.
6. Added exact HMLR INSPIRE-ID polygon matching with candidate-point-inside requirement.
7. Forbade fuzzy identity, point-only polygon and nearest-polygon promotion.
8. Added sequential HMLR polygon preparation orchestration.
9. Updated the main wrapper so numeric sampling cannot start before three exact HMLR polygons pass.
10. Aligned the same idempotent task across AAYS21 JSON, legacy plain text and portable `ai-tasks` pickup channels.
11. Published web operation rows 86-105.

## Current evidence

- Canonical source: `england_map_web/data/program_layer_matrix/topography.geojson`
- Canonical source feature count: `77970`
- Target candidate rows: `30762`, `46142`, `61522`
- Candidate target count: `3`
- Real candidate rows written: `0`
- Exact HMLR polygons written: `0`
- EA DTM polygon samples written: `0`
- OS Terrain 50 crosschecks written: `0`
- Existing automation tests/checks: `45/45`
- Source/automation contract accuracy: `4.0/4`
- Parcel measurement accuracy: `0/4_not_produced`
- Website operation rows: `105`

## Progress

- Planned operations: `121`
- Completed operations: `93`
- Blocked operations: `4`
- Pending operations: `3`
- Batch operation percent: `76.86`
- Batch increase this turn: `3.59`
- Overall completion percent: `78`
- Overall increase: `0`

## Blocker

`EXISTING_SINGLE_SHARED_RUNNER_CLAIM_PENDING;CANONICAL_CANDIDATE_SEED_EXTRACTION_PENDING_RUNNER;CURRENT_HMLR_AUTHORITY_GML_DOWNLOADS_PENDING;THREE_EXACT_HMLR_INSPIRE_ID_POLYGONS_PENDING;THREE_EA_DTM_1M_POLYGON_SAMPLES_PENDING;THREE_OS_TERRAIN50_CROSSCHECKS_PENDING;PORT_8012_HTTP_READBACK_PENDING`

## Next unverified step

`EXISTING_SHARED_RUNNER_CLAIM_ATTEMPT_009_THEN_STREAM_3_CANONICAL_SEEDS_DOWNLOAD_CURRENT_HMLR_GML_MATCH_3_EXACT_POLYGONS_AND_RUN_OFFICIAL_NUMERIC_SAMPLING`

No synthetic identifier, coordinate, geometry, polygon or elevation value was written. Safety flags remain false and `final_ready=false`.
