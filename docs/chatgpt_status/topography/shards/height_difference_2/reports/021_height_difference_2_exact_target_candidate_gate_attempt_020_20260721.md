# height_difference_2 — exact target candidate gate / attempt 020

- SLOT_ID: `height_difference_2`
- Parcel range: `30762-61522`
- Task: `aays1-height-difference-2-canonical-export-official-sampling-20260720`
- Attempt: `height-difference-2-20260721-020`
- Final ready: `false`

## Remote readback

The canonical persistent daemon heartbeat remains dated `2026-07-16T13:45:53.0433295Z`. The slot remains `unclaimed`. Restart, candidate, exact-HMLR, EA DTM1m, OS Terrain50 and port 8012 acceptance outputs remain absent. No runner execution or candidate row was inferred.

## Accuracy repair

The previous candidate extractor maintained nearest-row pools. If an exact target row was absent, it could select a nearby valid row even though downstream promotion requires exactly rows `30762`, `46142` and `61522`.

Attempt 020 removes that mismatch:

1. Only the three immutable `row_no` values are accepted.
2. Nearest-row fallback is forbidden and reported as `false`.
3. Missing, invalid and duplicate target occurrences fail closed.
4. Parcel IDs and HMLR INSPIRE IDs must be distinct.
5. Legacy point elevation values remain discarded.
6. Candidate extraction writes no polygon or numeric measurement.
7. The PowerShell carrier verifies the exact extractor Git blob before execution.

## Validation

`017_exact_target_candidate_gate_validation_20260721.json` records `18/18 PASS` across positive exact rows and negative nearest-only, missing, duplicate, invalid and duplicate-ID fixtures. Fixtures were not promoted to product data.

Cumulative deterministic/static validation: `289/289 PASS`.

## Progress

- Planned operations: `341`
- Completed operations: `302`
- Blocked operations: `6`
- Pending operations: `13`
- Batch progress: `88.56%`
- Batch increase: `0.40 percentage points`
- Overall completion: `78%`
- Overall increase: `0%`
- Website operation rows: `325`
- Candidate target / actual: `3 / 0`
- Exact HMLR polygons: `0`
- EA DTM1m polygon samples: `0`
- OS Terrain50 crosschecks: `0`

## First unverified step

`EXECUTE_EXISTING_PERSISTENT_F_DAEMON_THEN_CLAIM_ATTEMPT_020_AND_PROVE_EXACT_ROWS_30762_46142_61522`

## Blocker

`PERSISTENT_CANONICAL_F_DAEMON_RESTART_NOT_OBSERVED;SLOT_CLAIM_NOT_OBSERVED;THREE_EXACT_CANONICAL_CANDIDATE_SEEDS_PENDING;THREE_EXACT_HMLR_POLYGONS_PENDING;THREE_EA_DTM1M_POLYGON_SAMPLES_PENDING;THREE_OS_TERRAIN50_CROSSCHECKS_PENDING;PORT_8012_HTTP_READBACK_PENDING`

Safety flags remain false for fake data, database writes, migrations and production deployment.
