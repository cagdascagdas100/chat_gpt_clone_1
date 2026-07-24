# height_difference_2 — explicit official numeric gate — attempt 010

- Slot: `height_difference_2`
- Parcel range: `30762-61522`
- Existing task ID retained: `aays1-height-difference-2-canonical-export-official-sampling-20260720`
- Attempt: `height-difference-2-20260721-010`
- Final ready: `false`

## Completed in this checkpoint

1. Re-read checkpoint 9 and the unclaimed heartbeat without replaying completed work.
2. Revalidated the current official HMLR, Environment Agency and Ordnance Survey source contracts.
3. Added an explicit Environment Agency WCS 2.0.1 DTM 1m polygon sampler.
4. Locked EPSG:27700 GeoTIFF validation, valid-pixel polygon sampling and Q1/median/Q3 statistics.
5. Added an OS Terrain 50 ASCII Grid polygon crosschecker with BNG tile selection, selective archive extraction and SHA-256 capture.
6. Added an explicit numeric orchestrator: exact HMLR polygons -> EA DTM 1m -> OS Terrain 50.
7. Disabled automatic final promotion and retained mandatory human cross-source review.
8. Validated the new numeric gate with 25/25 fail-closed and positive fixture tests; no fixture values were committed or promoted.
9. Aligned the same idempotent task to attempt 010 across AAYS21 JSON, legacy plain text and portable `ai-tasks` pickup modes.
10. Published operation rows 106-125 to the manifest-driven website view.

## Official source contract

- HM Land Registry INSPIRE Index Polygons: July 2026 monthly GML files by local authority; unique Land Registry INSPIRE ID; indicative extent only.
- Environment Agency LiDAR Composite DTM 1m: WCS 2.0.1, EPSG:27700, Ordnance Datum Newlyn; valid polygon pixels produce Q1, median and Q3; no centroid promotion.
- OS Terrain 50: July 2026 OpenData release; ASCII Grid used only as a secondary coarse crosscheck.

## Current truthful state

- Candidate seed target: `3`
- Real candidate seed rows: `0`
- Exact HMLR polygon rows: `0`
- EA DTM 1m polygon sample rows: `0`
- OS Terrain 50 crosscheck rows: `0`
- Official numeric rows: `0`
- Automation tests: `70/70 PASS`
- Website operation rows: `125`
- Overall completion: `78%`

## Blocker

`EXISTING_SINGLE_SHARED_RUNNER_CLAIM_PENDING; CANONICAL_CANDIDATE_SEED_EXTRACTION_PENDING_RUNNER; CURRENT_HMLR_AUTHORITY_GML_DOWNLOADS_PENDING; THREE_EXACT_HMLR_INSPIRE_ID_POLYGONS_PENDING; THREE_EA_DTM_1M_POLYGON_SAMPLES_PENDING; OS_TERRAIN50_ARCHIVE_OR_ROOT_CONFIGURATION_PENDING; THREE_OS_TERRAIN50_CROSSCHECKS_PENDING; PORT_8012_HTTP_READBACK_PENDING`

No synthetic parcel identity, geometry, coordinate, elevation or completion state was written.
