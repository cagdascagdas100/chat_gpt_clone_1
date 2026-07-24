# AAYS1 site visibility bug report

Date: 2026-07-10
Page key: aays1

## Problem

The local matrix page does not render the aays1 layer rows in the main table. The screenshot shows the table still rendering another layer while the aays1 layer is only visible as a small status card.

## Expected behavior

The local matrix page must let the user select the aays1 layer and then see the produced rows directly in the main table.

## Known data state

- Verified rows available: 150
- Accuracy 4/4 rows: 150
- Manual review rows: 0
- Extra rows after 150: not available yet
- Final flag must stay false
- No fake rows may be created

## Required fix

1. Add the aays1 layer as a selectable table layer.
2. Render the 150 verified rows in the main table.
3. Show row-level source path, source URL, match/evidence text, accuracy, and review fields.
4. Show the source file paths used by the table.
5. Mark newly changed rows with a visible flag or badge.
6. Keep final_ready=false, fake_data=false, db_write=false, migration=false, production_deploy=false.
7. Create browser proof after the fix.

## Expected proof files

- docs/chatgpt_status/aays1/runner_outputs/138_site_visibility_fix.json
- docs/chatgpt_status/aays1/reports/138_site_visibility_fix_report.md
- docs/chatgpt_status/aays1/reports/138_browser_smoke.md
