# TerraYield 047 shared runner heartbeat check

page_key: AAYS_REAL_TOPOGRAPHY_PRODUCT
branch: aays-runner-v17-icon-work-20260603-232706
status: RUNNER_HEARTBEAT_MISSING_NOT_FINAL_READY
completion_percent: 78

## Checked
- Queue trigger exists: docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/queue/terrayield_047_distance_property_types_fixed_20260614.md
- Page-local automation exists: docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/automation/RUN_DISTANCE_047_SELF_CONTAINED_REPAIR.ps1
- Shared runner heartbeat was not found at docs/chatgpt_status/_shared/heartbeat/single_multi_page_runner_heartbeat.txt
- Expected smoke/status/output files are not visible in GitHub yet.

## Required next evidence
- docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/reports/terrayield_047_distance_property_types_apply_patch_smoke_<timestamp>.md
- docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/status/terrayield_047_distance_property_types_status_<timestamp>.md
- docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/runner_outputs/terrayield_047_distance_property_types_self_contained_repair_<timestamp>.txt

## Rule
No separate runner should be opened. The existing single shared runner should pick up the page-local queue item and execute the page-local automation script.
