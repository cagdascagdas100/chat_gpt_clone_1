# Gas Emissions Site Visibility Bug Report for Codex

Task ID: gas-emissions-135-site-visibility-bug-report-20260710
Page key: gas_emissions
Branch: codex/aays-single-runner-v5-20260706
Created at: 2026-07-10T09:18:00+03:00
Final ready: false

## Summary

The local matrix page is running, but the user cannot see the latest ChatGPT-added Gas Emissions evidence rows in the site. The page is displaying the stale `gas_emissions_updates/latest_changes.json` content instead of the current Gas Emissions marker/status + verified source-backed row CSV.

The current UI screenshot shows:

- URL: `127.0.0.1:8012/england_map_web/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html?refresh=portable`
- Selected layer: `Gas Emissions (3.533)`
- Top panel: `Gas Emissions yüklendi: 3.533 kayıt`
- Current-change card path: `gas_emissions_updates/latest_changes.json`
- Current-change card status: `BLOCKED_SINGLE_RUNNER_EVIDENCE_INCOMPLETE`
- Current-change card `source_row_gate_passed`: false
- Matrix table shows parcel rows, but does not show the latest ChatGPT-added verified rows from the marker/verified CSV sequence.

## Expected behaviour

When the user selects `Gas Emissions`, the web page should show the latest source-backed rows created by the Gas Emissions workflow, with sources and paths visible row-by-row.

The display should include, at minimum:

- `parcel_id`
- `parcel_ref`
- `emission_percent`
- `gas_emission_level`
- `risk_color`
- `confidence_percent`
- `accuracy_score_4`
- `source`
- `source_url`
- `source_date`
- `matching_method`
- `calculation_explanation`
- `needs_manual_review`
- `changed_in_latest_run`
- `verified_rows_path`
- `latest_changes_path`
- `fixture_rows_path`
- status/final flags

Newly added rows must be visually distinguishable from old rows. Suggested UI rule:

- Highlight rows where `changed_in_latest_run === true`.
- Add a `Yeni` / `Latest` badge for rows loaded from the current marker's `verified_rows_path`.
- Show a compact source/path panel above the latest rows.

## Actual behaviour

The page reads and displays only:

```text
outputs/england_program_parcel_matrix_20260629/gas_emissions_updates/latest_changes.json
```

That file is currently stale/blocker content:

```json
{
  "layer": "Gas Emissions",
  "program_output": "Gas Emission Level",
  "status": "BLOCKED_SINGLE_RUNNER_EVIDENCE_INCOMPLETE",
  "source_row_gate_passed": false,
  "verification_score_after": "2/4",
  "final_ready": false
}
```

The active marker is much newer and source-backed:

```text
england_map_web/data/program_layer_matrix/gas_emissions_status_latest.json
```

Latest marker status at report time:

```json
{
  "status": "TRUSTED_SOURCE_ROWS_VISIBLE_UK2024_FOSSIL_RECORDS",
  "source_row_gate_passed": true,
  "current_visible_change_rows": 4,
  "cumulative_trial_row_count": 114,
  "verification_score_after": "3.31/4",
  "verified_rows_path": "outputs/england_program_parcel_matrix_20260629/gas_emissions_updates/verified_source_backed_rows_uk2024_fossil_record_guardian_carbonbrief_20260710.csv"
}
```

## Root cause hypothesis

1. The browser card is wired to `gas_emissions_updates/latest_changes.json` only.
2. `latest_changes.json` is repeatedly overwritten by stale single-runner output with `BLOCKED_SINGLE_RUNNER_EVIDENCE_INCOMPLETE`.
3. The page does not fallback to `england_map_web/data/program_layer_matrix/gas_emissions_status_latest.json`.
4. The page does not load the CSV pointed to by `verified_rows_path` in the current marker.
5. The lower parcel matrix shows program layer parcel records, but not the latest source-backed evidence rows produced by ChatGPT.

## Required fix

Implement a Gas Emissions latest-source row panel using this priority order:

1. Read `england_map_web/data/program_layer_matrix/gas_emissions_status_latest.json`.
2. If marker has `verified_rows_path`, fetch and parse that CSV.
3. Render the CSV rows in the `Gas Emissions - Güncel Değişiklikler` card or a new `Gas Emissions - Kaynaklı Son Satırlar` card.
4. Keep `latest_changes.json` visible only as secondary/debug information when it is stale.
5. If `latest_changes.status` starts with `BLOCKED_` but marker `source_row_gate_passed === true`, show a warning:
   - `latest_changes stale; marker/verified rows are authoritative for latest source-backed rows`.
6. Show the marker paths and CSV paths in the UI:
   - `gas_emissions_status_latest.json`
   - `verified_rows_path`
   - `latest_changes_path`
   - `fixture_rows_path`
7. Highlight current rows:
   - `changed_in_latest_run === true`
   - rows from the current marker CSV
8. Do not change DB, migrations, production deploy, or final flags.

## Acceptance criteria

The local site at port 8012 must show:

- Selected layer remains `Gas Emissions`.
- A latest-source-backed rows panel appears.
- The panel uses `gas_emissions_status_latest.json` as the current marker.
- The panel loads `verified_source_backed_rows_uk2024_fossil_record_guardian_carbonbrief_20260710.csv` or whatever `verified_rows_path` points to at runtime.
- The four latest rows are visible with source/source_url/source_date/matching_method/calculation_explanation.
- The UI clearly marks these rows as new/latest.
- `fake_data=false` remains visible.
- `final_ready=false` remains visible.
- Existing parcel matrix is not removed.
- No new runner is started.
- No C:\ canonical path is introduced.

## Guardrails

Keep these flags unchanged unless separately proven:

```json
{
  "final_ready": false,
  "product_final_ready": false,
  "fake_data": false,
  "db_write": false,
  "migration": false,
  "production_deploy": false
}
```

Use only the existing F portable single runner:

```text
F:\TerraYield_AAYS_Portable\RUN_AAYS_STABLE_RUNNER_FROM_THIS_DISK.cmd
```

## Next action for Codex/runner

Fix the frontend data binding/fallback so the local site reads marker + verified rows and surfaces the newest source-backed Gas Emissions rows row-by-row. After the UI proof is written, resume normal Gas Emissions data expansion.
