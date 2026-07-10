# 159 Distance Property Types / Parcel Label visibility artifact sync blocker

Date: 2026-07-10
Page key: aays1
Layer: Distance to Nearby Property Types / Parcel Label
Branch: codex/aays-single-runner-v5-20260706
Canonical runner: F:\TerraYield_AAYS_Portable\RUN_AAYS_STABLE_RUNNER_FROM_THIS_DISK.cmd

## Observed status

The user reported that Codex fixed the Parcel Label / Distance Property Types visibility binding and asked ChatGPT to verify these files:

- england_map_web/data/program_layer_matrix/distance_property_types_visible_rows_latest.json
- england_map_web/data/program_layer_matrix/distance_property_types_status_latest.json
- england_map_web/data/distance_property_types/distance_property_types_verified.csv
- docs/chatgpt_status/distance_property_types/reports/141_distance_property_types_site_visibility_fix_report_20260710.md

GitHub verification from ChatGPT found:

- `england_map_web/data/distance_property_types/distance_property_types_verified.csv` exists and contains the real 6 source-backed pilot rows.
- `england_map_web/data/program_layer_matrix/distance_property_types_visible_rows_latest.json` returned 404 on the target branch.
- `england_map_web/data/program_layer_matrix/distance_property_types_status_latest.json` returned 404 on the target branch.
- `docs/chatgpt_status/distance_property_types/reports/141_distance_property_types_site_visibility_fix_report_20260710.md` returned 404 on the target branch.
- Repository search for `distance_property_types_visible_rows_latest` returned no result.
- Repository search for `141_distance_property_types_site_visibility_fix_report_20260710` returned no result.

## Impact

Do not continue bulk candidate expansion until the site visibility artifacts are synced to GitHub and available to the F portable web root. The current verified CSV proves only the real 6 source-backed pilot rows. The previously prepared 88 candidate rows must not be treated as completed.

## Required fix

Create or push the missing visibility artifacts to branch `codex/aays-single-runner-v5-20260706` and F portable web root:

1. `england_map_web/data/program_layer_matrix/distance_property_types_visible_rows_latest.json`
2. `england_map_web/data/program_layer_matrix/distance_property_types_status_latest.json`
3. `docs/chatgpt_status/distance_property_types/reports/141_distance_property_types_site_visibility_fix_report_20260710.md`

The status JSON must clearly separate:

- `verified_visible_rows`: 6
- `prepared_pending_rows`: 88
- `completed_bulk_rows`: 0 unless real completed status files exist
- `final_ready`: false
- `fake_data`: false

## Site acceptance checks

- Program Parcel Layer Matrix dropdown includes Distance to Nearby Property Types / Parcel Label.
- The visible rows JSON is loaded by the site.
- The status JSON is loaded by the site.
- The site shows the real 6 source-backed pilot rows row-by-row with source URL/path, accuracy score, and changed marker.
- The site may show prepared rows as pending only, but must not count them as completed.
- A Distance Property Types / Parcel Label `Guncel Degisiklikler` panel exists.
- No new runner is started.
- No parallel runner is used.
- `final_ready=false` remains unchanged.
- `fake_data=false`, `db_write=false`, `migration=false`, `production_deploy=false` remain unchanged.

## Current decision

ChatGPT paused new candidate production at this step because the user specifically asked to see results row-by-row on the site. Resume real source candidate production only after these visibility artifacts are present and visible.
