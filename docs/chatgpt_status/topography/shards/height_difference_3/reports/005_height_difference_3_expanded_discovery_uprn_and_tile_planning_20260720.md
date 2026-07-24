# height_difference_3 — Expanded canonical discovery, UPRN and tile planning

- Slot: `height_difference_3`
- Canonical row range: `61523-92283`
- Row count: `30,761`
- Checkpoint advanced: `4 -> 5`
- Final ready: `false`

## Work completed

1. Added a bounded canonical-matrix discovery script that checks known output paths, follows manifest references, optionally probes the existing local port `8012`, and rejects files that do not contain the explicit complete row range.
2. Locked anti-fabrication validation: row numbers are never inferred from file order; duplicate or out-of-range rows fail; at least three source-backed official identities are required before starter selection.
3. Added exact UPRN coordinate enrichment using OS Open UPRN fields `UPRN`, `X_COORDINATE`, `Y_COORDINATE`, `LATITUDE`, and `LONGITUDE`. Fuzzy address or nearest-point matching is forbidden.
4. Added deterministic HMLR local-authority download-link, Environment Agency DTM catalogue-query, and OS Terrain 50 10 km tile-key planning for the first three real candidates.
5. Published an expanded ten-step contract for the existing single shared runner. No new runner or competing shard claim was created.
6. Published website operation rows `39-68`.

## Non-production automation validation

- Canonical discovery full-range test: exact `30,761` rows accepted and chained to the query preparer.
- Missing-input test: failed closed with zero elevation measurements.
- Exact-UPRN streaming-join test: `30,761` mock rows joined with zero unresolved rows.
- British National Grid tile-key tests: known coordinate examples produced `TQ38`, `SU41`, and `SJ39`.

These validation fixtures were temporary and were not committed, published as parcel evidence, or counted as measured rows.

## Current evidence counts

- Official/source candidates: `5`
- High-confidence candidates: `4`
- Source-contract score: `3.9/4`
- Automation-validation score: `4/4`
- Real parcel candidates selected: `0`
- Canonical shard rows exported: `0`
- HMLR boundary matches: `0`
- EA DTM samples: `0`
- OS Terrain 50 crosschecks: `0`
- Measured parcel rows: `0`
- Cumulative website operation rows: `68`

## Cycle metrics

- Operations processed: `30/30`
- Operations completed: `25`
- Operations blocked by missing real inputs: `5`
- Cycle processed percent: `100%`
- Cycle success percent: `83.33%`
- Overall product completion: `78%`
- Product percent increase: `0`

## Actual blocker

`CANONICAL_8012_MATRIX_SHARD_EXPORT_REQUIRED; ROW_NO_PARCEL_ID_OFFICIAL_IDS_COORDINATES_OR_UPRN_EXPORT_MISSING; REAL_SHARD_PARCEL_CANDIDATES_REQUIRED; REAL_BOUNDARY_AND_EA_DTM_SAMPLE_REQUIRED; OS_TERRAIN50_INDEPENDENT_CROSSCHECK_REQUIRED`

## First unverified step

`RUN_005_CANONICAL_DISCOVERY_ON_EXISTING_F_PORTABLE_RUNNER_THEN_SELECT_THREE_REAL_ROWS`

No measured value may be published before canonical parcel identity, source-backed location or boundary, one Environment Agency DTM 1 m sample, and an independent OS Terrain 50 crosscheck are present.

Safety flags remain unchanged: `fake_data=false`, `db_write=false`, `migration=false`, `production_deploy=false`.
