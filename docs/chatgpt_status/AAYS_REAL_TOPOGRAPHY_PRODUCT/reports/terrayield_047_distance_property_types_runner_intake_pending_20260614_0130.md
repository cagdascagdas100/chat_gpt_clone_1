# TerraYield 047 Distance Property Types runner intake pending

page_key: AAYS_REAL_TOPOGRAPHY_PRODUCT
branch: aays-runner-v17-icon-work-20260603-232706
status: NOT_FINAL_READY
completion_percent: 92

## What is ready
- Active queue file exists and remains the authoritative task.
- The active queue points to the page-local automation script.
- The old current-task pointer is superseded.
- The page automation is prepared to write report, status, and raw runner output files.
- The shared single-runner policy requires evidence under this same page key before FINAL_READY.

## Current blocker
No runner-produced smoke report, status report, or raw runner log has appeared after the latest successful queue retry.

This means progress is blocked at runner intake / poller execution evidence, not at product acceptance yet.

## Why the percentage cannot honestly reach 100
FINAL_READY requires proof that:
- the endpoint returns parcel polygon features;
- all six distance metrics are present and non-null;
- popup/right-panel fields satisfy the contract;
- schema and UI acceptance pass;
- the evidence is written by the page automation under this page key.

Those files are still missing.

## Next expected files
- docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/reports/terrayield_047_distance_property_types_apply_patch_smoke_<timestamp>.md
- docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/status/terrayield_047_distance_property_types_status_<timestamp>.md
- docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/runner_outputs/terrayield_047_distance_property_types_self_contained_repair_<timestamp>.txt

## Forward blocker decision tree
1. If no report appears: runner intake / poller / heartbeat blocker.
2. If report says endpoint unavailable: backend route or service startup blocker.
3. If report says empty FeatureCollection: data availability blocker.
4. If report says missing/null metrics: metric population blocker.
5. If report says popup/schema missing: UI or contract blocker.
6. If all checks pass: FINAL_READY can be set to 100.
