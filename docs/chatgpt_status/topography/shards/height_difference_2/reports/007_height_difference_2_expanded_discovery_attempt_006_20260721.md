# height_difference_2 — Expanded Discovery Attempt 006

- Slot: `height_difference_2`
- Parcel range: `30762-61522`
- Existing task: `aays1-height-difference-2-canonical-export-official-sampling-20260720`
- Checkpoint: `6`
- Runner policy: existing single shared runner only
- final_ready: `false`

## Completed in this checkpoint

1. Re-read remote branch, current task, slot heartbeat and expected output.
2. Confirmed the task remained selected but unclaimed; no runner output existed.
3. Reviewed the same-layer `height_difference_3` fail-closed discovery method only; no shard-3 parcel data was copied or claimed.
4. Added a hash-locked three-script bundle for:
   - GitHub REST tree discovery of an explicit canonical `30762-61522` shard,
   - OS Terrain 50 HTTPS URL/HAR capture and ZIP/ASCII validation,
   - sequential orchestration before the existing official-sampling payload.
5. Integrated the bundle into the existing Python entrypoint.
6. Routed the legacy PowerShell pickup through the same entrypoint.
7. Updated the same idempotent task to attempt `006`; no new task, runner or parallel execution was created.
8. Recorded `8/8` local fail-closed automation tests. Fixtures were not committed and no fixture value was promoted.
9. Changed the web operations page to a manifest-driven loader and published operations `51-60`.

## Metrics

- Completed operations: `52/75`
- Batch progress: `69.33%`
- Batch increase: `+3.18%`
- Overall layer progress: `78%`
- Overall increase: `+0%`
- Visible web operation rows: `60`
- Official source candidates: `3`
- Source contracts upgraded: `3`
- Source-contract accuracy: `4.0/4`
- Automation validation: `4.0/4` (`8/8` tests)
- Real parcel candidates: `0`
- Real HMLR matches: `0`
- EA DTM numeric parcel samples: `0`
- OS Terrain 50 parcel crosschecks: `0`

## Current blocker

`EXISTING_SINGLE_SHARED_RUNNER_CLAIM_PENDING; CANONICAL_8012_MATRIX_SHARD_EXPORT_PENDING; OS_TERRAIN50_LIVE_DOWNLOAD_URL_OR_ARCHIVE_PENDING; THREE_REAL_HMLR_BOUNDARY_MATCHES_PENDING; THREE_EA_DTM_1M_POLYGON_SAMPLES_PENDING; THREE_OS_TERRAIN50_CROSSCHECKS_PENDING; PORT_8012_HTTP_READBACK_PENDING`

The preparation work is real and committed, but the external F portable shared runner has not produced a lease, heartbeat or output. Therefore no measured parcel value and no overall percentage increase were claimed.

## Next unverified step

`EXISTING_SHARED_RUNNER_CLAIM_ATTEMPT_006_THEN_RUN_EXPANDED_DISCOVERY_AND_ORIGINAL_OFFICIAL_SAMPLING`

## Safety

- fake_data: `false`
- db_write: `false`
- migration: `false`
- production_deploy: `false`
- final_ready: `false`
