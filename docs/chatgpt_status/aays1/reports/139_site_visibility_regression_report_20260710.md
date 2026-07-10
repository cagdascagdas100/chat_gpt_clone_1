# AAYS1 site visibility regression report

Date: 2026-07-10
Page key: aays1

## Observed issue

The local matrix page at 127.0.0.1:8012 still shows the main selector and main table on `Gas Emissions`. The aays1 layer information is only visible in the upper status card, not in the main row table.

## Data state in repo

- `england_map_web/data/program_layer_matrix/security_public_safety_visible_rows.json` says 150 visible rows are available.
- `england_map_web/data/program_layer_matrix/security_public_safety_visible_status.json` says progress is 99 percent and final remains false.
- No fake rows are allowed.
- `final_ready` must stay false.

## Required local page fix

1. Add the aays1 layer to the main layer selector.
2. When aays1 is selected, render the 150 rows in the main table.
3. Show row source path, source URL, evidence or match note, accuracy, review status, and new-row marker.
4. Ensure the card and the main table read from the same F portable data paths.
5. Add browser proof after the fix.

## Expected proof

- `docs/chatgpt_status/aays1/runner_outputs/139_site_visibility_regression_fix.json`
- `docs/chatgpt_status/aays1/reports/139_browser_smoke.md`

## Guardrails

Do not create fake rows. Do not set final_ready true. Do not change db, migration, or production deploy flags.