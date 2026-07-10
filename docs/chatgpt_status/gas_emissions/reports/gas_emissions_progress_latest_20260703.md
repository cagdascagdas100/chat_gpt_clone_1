# Gas Emissions Progress Latest

updated_at=2026-07-10T03:18:00+03:00
final_ready=False
verification_score_before=2.75/4
verification_score_after=2.9/4
rows_added_this_run=5
rows_added_this_chat_session=12
visible_change_rows=5
cumulative_trial_row_count=59
source=Guardian summary of UK official 2024 carbon figures
source_url=https://www.theguardian.com/environment/2025/mar/27/uk-carbon-emissions-fell-by-4-in-2024-official-figures-show
source_method=UK 2024 official carbon figure summary mapped to Gas Emissions display fields
csv_updated=docs/chatgpt_status/gas_emissions/fixtures/gas_emissions_verified_rows_template_20260703.csv
latest_changes_updated=outputs/england_program_parcel_matrix_20260629/gas_emissions_updates/latest_changes.json
site_marker_updated=england_map_web/data/program_layer_matrix/gas_emissions_status_latest.json
fake_data=False
db_write=False
migration=False
production_deploy=False
blocker_count=3

## Added Rows This Run

- GAS_UK2024_TOTAL_CARBON: 96 / High / orange
- GAS_UK2024_TRANSPORT_SHARE: 100 / Very High / red
- GAS_UK2024_TOTAL_DROP: 96 / High / orange
- GAS_UK2024_BUILDINGS_TREND: 100 / Very High / red
- GAS_UK2024_REDUCTION_FROM_1990: 46 / Medium / yellow

## Remaining Blockers

- parcel_specific_binding_pending
- local_8020_browser_smoke_pending
- popup_right_panel_field_proof_pending

## Next Action

Use the existing F portable single runner only. Pull this branch, refresh the 8020 matrix site, verify Gas Emissions row display, then continue parcel binding. Keep final_ready=false.
