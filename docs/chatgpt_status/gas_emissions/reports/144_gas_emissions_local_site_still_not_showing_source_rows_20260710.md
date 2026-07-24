# Gas Emissions Local Site Visibility Still Blocked

Task ID: gas-emissions-144-local-site-still-not-showing-source-rows-20260710
Branch: codex/aays-single-runner-v5-20260706
Created at: 2026-07-10T10:05:00+03:00
Final ready: false

## Summary

The user provided a fresh local browser screenshot. The Gas Emissions page is still not showing the latest source-backed rows row-by-row with source paths. The visible card still reads `gas_emissions_updates/latest_changes.json` and still displays stale `BLOCKED_SINGLE_RUNNER_EVIDENCE_INCOMPLETE` content.

New gas/emission source expansion remains paused until the local web page shows the current source-backed rows correctly.

## Proof checked

1. `england_map_web/data/program_layer_matrix/gas_emissions_status_latest.json`
   - Still points to the older 4-row fossil-record marker.
   - `current_visible_change_rows`: 4
   - `verification_score_after`: 3.31/4
   - `final_ready`: false

2. `england_map_web/data/program_layer_matrix/gas_emissions_visible_rows_latest.json`
   - Exists, but reports 24 visible rows, not 120.
   - `status`: OFFICIAL_VISIBLE_SAMPLE_ROWS_EXPANDED_24
   - `source_row_accuracy_score_4`: 3.4/4
   - `final_ready`: false
   - `fake_data`: false

3. `england_map_web/data/program_layer_matrix/gas_emissions.geojson`
   - GitHub fetch returned empty content.
   - This does not prove the claimed 3533 Gas Emissions features from branch content.

4. `docs/chatgpt_status/gas_emissions/reports/142_gas_emissions_site_visibility_fix_report_20260710.md`
   - Fetch returned 404 Not Found.

## Required fix

- Add/fix a dedicated `Gas Emissions - Kaynakli Son Satirlar` panel.
- The panel must read the current marker and visible rows proof, not only stale `latest_changes.json`.
- Render source-backed rows row-by-row.
- Show row id, year/period, sector/subsector, greenhouse gas, emission value, source, source path or URL, matching method, confidence, accuracy, manual-review flag, and latest/new badge.
- Mark newly added rows visually distinct from old parcel matrix rows.
- If 120 rows are claimed, `gas_emissions_visible_rows_latest.json` must report and contain/reference 120 rows. Otherwise keep the claim at 24.
- Repoint `gas_emissions_status_latest.json` to the current visible rows proof or add `visible_rows_path`.
- Make `gas_emissions.geojson` non-empty in branch proof or add a separate feature-count proof file for 3533 features.
- Push/create the missing 142 visibility-fix report or correct the handoff path.
- Keep `final_ready=false`, `product_final_ready=false`, `fake_data=false`, `db_write=false`, `migration=false`, `production_deploy=false`.

## Blockers

- local_site_still_shows_stale_latest_changes_card
- site_does_not_show_source_backed_rows_row_by_row
- status_marker_still_points_to_old_4_row_csv
- visible_rows_count_24_not_120
- gas_emissions_geojson_empty_from_github_fetch
- missing_142_visibility_fix_report
- parcel_specific_binding_pending
- browser_smoke_pending_after_fix

## Resume condition

Resume real internet-sourced gas/emission expansion only after the local page and GitHub proof both show the current source-backed rows row-by-row with paths and latest-row highlighting. Until then, new rows added: 0.
