# height_difference_2 — canonical source and streaming candidate extraction

- Slot: `height_difference_2`
- Parcel range: `30762-61522`
- Checkpoint: `8`
- Task: `aays1-height-difference-2-canonical-export-official-sampling-20260720`
- Attempt: `height-difference-2-20260721-008`
- Final ready: `false`

## New verified progress

1. Re-read checkpoint 7, status, heartbeat and runner outputs without replaying completed work.
2. Confirmed the existing F portable runner has still not emitted a claim heartbeat or task output.
3. Identified the committed canonical Topography source at `england_map_web/data/program_layer_matrix/topography.geojson`.
4. Verified the source blob SHA `ca95400a5644f77a79cbaf47b2c2d611d3777a55` and repository integration evidence for 77,970 features.
5. Confirmed the source has explicit `row_no`, `parcel_id`, `hmlr_inspire_id`, HMLR area and HMLR coordinates.
6. Added a standard-library streaming extractor for explicit rows `30762-61522`; file-order inference is forbidden.
7. Candidate selection targets the start, midpoint and end of the shard and requires three distinct HMLR INSPIRE IDs with `4/4` HMLR identity/location accuracy.
8. Existing `2/4` point Topography values are discarded from the candidate output and are not promoted to official measurements.
9. Added a sequential candidate-then-sampling wrapper and routed AAYS21 JSON, legacy text and portable ai-task pickup modes through it.
10. Validation is `16/16 PASS` for the new extractor/wrapper and `24/24 PASS` cumulatively with the prior expanded-discovery validation.
11. Published web operation rows `70-85`; the manifest now exposes 85 operation rows.

## Metrics

- Planned operations: 101
- Completed operations: 74
- Blocked operations: 4
- Pending operations: 2
- Batch progress: 73.27%
- Batch increase: 2.68 percentage points
- Overall layer progress: 78%
- Overall increase: 0 percentage points
- Official source candidates: 3
- Canonical committed source files: 1
- Canonical source features: 77,970
- Candidate seed target: 3
- Real candidate seed rows produced: 0
- HMLR polygon rows produced: 0
- Official numeric measurements produced: 0
- Web operation rows: 85
- Source/automation accuracy: 4.0/4
- Parcel measurement accuracy: 0/4, not produced

## Current blocker

`EXISTING_SINGLE_SHARED_RUNNER_CLAIM_PENDING; CANONICAL_CANDIDATE_SEED_EXTRACTION_PENDING_RUNNER; OS_TERRAIN50_LIVE_DOWNLOAD_URL_OR_ARCHIVE_PENDING; THREE_REAL_HMLR_BOUNDARY_MATCHES_PENDING; THREE_EA_DTM_1M_POLYGON_SAMPLES_PENDING; THREE_OS_TERRAIN50_CROSSCHECKS_PENDING; PORT_8012_HTTP_READBACK_PENDING`

## First unverified step

`EXISTING_SHARED_RUNNER_CLAIM_ATTEMPT_008_THEN_STREAM_3_CANONICAL_HMLR_SEEDS_AND_RUN_OFFICIAL_POLYGON_SAMPLING`

No synthetic parcel identity, coordinate, boundary or elevation was written. No database write, migration or production deployment was performed.
