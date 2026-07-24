# Gas Emissions Visibility Fix Verification - Blocked

Task ID: gas-emissions-143-visibility-fix-verification-blocked-20260710
Page key: gas_emissions
Branch: codex/aays-single-runner-v5-20260706
Created at: 2026-07-10T09:40:00+03:00
Final ready: false

## Summary

Codex reported that the Gas Emissions visibility binding was fixed, with 3,533 program-layer GeoJSON gas features and 120 visible panel sample rows. The GitHub proof files do not fully confirm that state on branch `codex/aays-single-runner-v5-20260706`.

New source-backed gas/emission expansion must remain paused until the visibility proof mismatch is resolved.

## Files checked

### 1. england_map_web/data/program_layer_matrix/gas_emissions_status_latest.json

Fetched successfully.

Current relevant values:

```json
{
  "status": "TRUSTED_SOURCE_ROWS_VISIBLE_UK2024_FOSSIL_RECORDS",
  "source_row_gate_passed": true,
  "current_visible_change_rows": 4,
  "cumulative_trial_row_count": 114,
  "verification_score_after": "3.31/4",
  "final_ready": false,
  "verified_rows_path": "outputs/england_program_parcel_matrix_20260629/gas_emissions_updates/verified_source_backed_rows_uk2024_fossil_record_guardian_carbonbrief_20260710.csv"
}
```

Issue: this marker still points to the older 4-row fossil-record marker CSV, not the new 120-row visible panel sample proof.

### 2. england_map_web/data/program_layer_matrix/gas_emissions_visible_rows_latest.json

Fetched successfully.

Current relevant values:

```json
{
  "status": "OFFICIAL_VISIBLE_SAMPLE_ROWS_EXPANDED_24",
  "source": "GOV.UK DESNZ 2005 to 2023 local authority greenhouse gas emissions dataset",
  "visible_row_count": 24,
  "source_row_accuracy_score_4": "3.4/4",
  "final_ready": false,
  "fake_data": false
}
```

Issue: Codex/user handoff says 120 sample rows are bound, but the checked file reports `visible_row_count: 24` and status `OFFICIAL_VISIBLE_SAMPLE_ROWS_EXPANDED_24`.

### 3. england_map_web/data/program_layer_matrix/gas_emissions.geojson

Fetched, but GitHub file content was empty in both UTF-8 and base64 fetch attempts.

Issue: this does not prove the reported 3,533 GeoJSON gas features from repository content. The local browser may show 3,533 from generated/local data, but the requested branch proof file did not validate it.

### 4. docs/chatgpt_status/gas_emissions/reports/142_gas_emissions_site_visibility_fix_report_20260710.md

Fetch result: 404 Not Found on the requested branch and default fetch attempt. Repository search for `142_gas_emissions_site_visibility_fix_report_20260710` returned no result.

Issue: the named Codex visibility-fix report is missing or not pushed to the expected path/branch.

## Required Codex/runner fix

1. Push or create `docs/chatgpt_status/gas_emissions/reports/142_gas_emissions_site_visibility_fix_report_20260710.md` at the requested path.
2. Update `gas_emissions_visible_rows_latest.json` to match the claimed proof, or correct the claim:
   - If there are 120 visible rows, `visible_row_count` must be 120 and rows array should contain or reference those 120 rows.
   - If only 24 rows are bound, keep 24 and do not claim 120.
3. Update `gas_emissions_status_latest.json` so it references the current visible rows proof, not the older 4-row fossil-record CSV.
4. Ensure `gas_emissions.geojson` is non-empty in GitHub branch proof and contains/proves the 3,533 gas features, or write a separate proof file with exact feature count and generation path.
5. Keep `final_ready=false`, `fake_data=false`, `db_write=false`, `migration=false`, `production_deploy=false`.
6. Do not use stale `latest_changes.json` as final evidence.

## Current blocker state

- `visibility_fix_proof_mismatch`
- `visible_rows_count_mismatch_24_vs_120_claim`
- `missing_142_fix_report`
- `gas_emissions_geojson_empty_or_unverified_from_github_fetch`
- `status_marker_not_repointed_to_visible_rows_latest`
- `parcel_specific_binding_pending`
- `local_8012_browser_smoke_pending_after_fix`

## Resume condition

Resume real source-backed gas/emission expansion only after GitHub proof confirms:

- `gas_emissions_visible_rows_latest.json` row count and rows are consistent with the UI claim,
- `gas_emissions_status_latest.json` points to the current visible rows proof,
- `gas_emissions.geojson` feature count is proven,
- 142 fix report exists at the expected path,
- final flags remain false.
