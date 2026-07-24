# Parcel Label / Distance Property Types Site Visibility User Recheck Report

Date: 2026-07-10
Page key: aays1
Layer: Distance to Nearby Property Types / Parcel Label
Observed URL: http://127.0.0.1:8012/england_map_web/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html?refresh=portable
Canonical runner: F:\TerraYield_AAYS_Portable\RUN_AAYS_STABLE_RUNNER_FROM_THIS_DISK.cmd

## User-observed problem

The user screenshot still shows the Program Parcel Layer Matrix opened on `Gas Emissions (3,533)`.
The user cannot see Parcel Label / Distance Property Types rows on the web page.
The user specifically requires the generated rows to be visible row-by-row on the site, including source URLs, source paths, evidence fields, report/payload paths, accuracy values, and a clear marker for newly prepared or pending rows.

## Current GitHub proof

- Runner heartbeat is active, but `processed_task_count` is still `0`.
- `distance_property_types_verified.csv` exists and contains 6 real source-backed pilot rows.
- The visibility JSON/status artifacts requested for the web matrix were not found on the target branch in the latest ChatGPT check.
- The prepared 88 bulk rows must remain pending and must not be counted as completed without real runner completed outputs.

## Required fixes for Codex / runner

1. Ensure the Program Parcel Layer Matrix dropdown includes and can load `Distance to Nearby Property Types / Parcel Label`.
2. Ensure the site does not remain on `Gas Emissions` when the user is trying to inspect Parcel Label output.
3. Create or sync these files to the target branch and the F portable web root:
   - `england_map_web/data/program_layer_matrix/distance_property_types_visible_rows_latest.json`
   - `england_map_web/data/program_layer_matrix/distance_property_types_status_latest.json`
   - `docs/chatgpt_status/distance_property_types/reports/141_distance_property_types_site_visibility_fix_report_20260710.md`
4. Show the real 6 pilot rows from `england_map_web/data/distance_property_types/distance_property_types_verified.csv` row-by-row on the site.
5. Add or expose a `Distance Property Types / Parcel Label - Guncel Degisiklikler` panel.
6. Show at least these columns in the table or row detail view:
   - parcel_id
   - parcel_ref
   - selected_property_type
   - selected_color_category
   - accuracy_score_4
   - accuracy_label_4
   - confidence_percent if available
   - source_url
   - source_path
   - payload_path
   - queue_task_path
   - official_source_evidence
   - web_source_evidence
   - map_source_evidence
   - matching_method
   - needs_manual_review
   - changed_in_latest_run
   - change_reason
   - candidate_status
7. Mark rows clearly:
   - verified pilot rows: `VISIBLE_PILOT_SOURCE_BACKED`
   - prepared but not completed rows: `PENDING_RUNNER` or `NEW_PREPARED`
   - completed rows only after real completed status exists: `COMPLETED_VISIBLE`
8. Do not mark the 88 prepared rows as completed.
9. If runner cannot process the queued Parcel Label tasks, write an explicit blocker output explaining the failure.

## Acceptance checks

- The user can select Parcel Label / Distance Property Types from the site and see 6 real pilot rows.
- Each visible row includes source URL/path and accuracy score.
- New/pending rows are visually distinct from completed rows.
- The 88 prepared rows remain pending unless real completed files exist.
- `single_runner_only=true` remains true.
- `new_runner=false`, `parallel_runner=false` remain false.
- `fake_data=false`, `db_write=false`, `migration=false`, `production_deploy=false` remain false.
- `final_ready=false` remains false.

## Current action

Candidate expansion is paused until the site visibility path is fixed and verifiable.
