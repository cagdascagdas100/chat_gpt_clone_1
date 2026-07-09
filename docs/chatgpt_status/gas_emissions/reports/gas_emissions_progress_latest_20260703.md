# Gas Emissions Progress Latest

updated_at=2026-07-10T02:58:00+03:00
final_ready=False
verification_score_before=2.5/4
verification_score_after=2.75/4
rows_added_this_run=7
visible_change_rows=7
source=Guardian summary of UK government greenhouse gas emissions figures for 2022 sector shares
source_url=https://www.theguardian.com/environment/2024/feb/06/uks-emissions-fell-slightly-in-2022-but-transport-and-homes-still-biggest-emitters
source_method=UK sector shares normalised against largest listed sector for green-to-red Gas Emissions display
csv_updated=docs/chatgpt_status/gas_emissions/fixtures/gas_emissions_verified_rows_template_20260703.csv
latest_changes_updated=outputs/england_program_parcel_matrix_20260629/gas_emissions_updates/latest_changes.json
site_marker_updated=england_map_web/data/program_layer_matrix/gas_emissions_status_latest.json
fake_data=False
db_write=False
migration=False
production_deploy=False
blocker_count=3

## Added Rows

- GAS_UK2022_DOMESTIC_TRANSPORT: 100 / Very High / red
- GAS_UK2022_HOMES_PRODUCT_USE: 71 / High / orange
- GAS_UK2022_ELECTRICITY_SUPPLY: 50 / Medium / yellow
- GAS_UK2022_INDUSTRY: 50 / Medium / yellow
- GAS_UK2022_AGRICULTURE: 43 / Medium / yellow
- GAS_UK2022_FUEL_SUPPLY: 29 / Low / light_green
- GAS_UK2022_WASTE: 14 / Very Low / green

## Remaining Blockers

- parcel_specific_binding_pending
- local_8020_browser_smoke_pending
- popup_right_panel_field_proof_pending

## Next Action

Use the existing F portable single runner only. Pull this branch, refresh the 8020 matrix site, verify Gas Emissions row display, then continue parcel binding. Keep final_ready=false.
