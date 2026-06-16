# TerraYield 047 Runner Blocked Watchdog

page_key: AAYS_REAL_TOPOGRAPHY_PRODUCT
branch: aays-runner-v17-icon-work-20260603-232706
status: RUNNER_BLOCKED_WATCHDOG
completion_percent: 99.8
final_ready: false
power_shell_required: false
wait_minutes: 10

## Current live task
current_task: docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/current-task/terrayield_047_distance_property_types_fixed_20260614.md
current_task_retry: 20260616T0040Z
automation: docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/automation/RUN_DISTANCE_047_SELF_CONTAINED_REPAIR.ps1

## Blocker
single_shared_runner_has_not_published_outputs_after_current_task_retry: true
missing_smoke_report: true
missing_raw_runner_output: true
missing_shared_heartbeat: true

## Expected output files
expected_smoke_report: docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/reports/terrayield_047_distance_property_types_apply_patch_smoke_<timestamp>.md
expected_raw_output: docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/runner_outputs/terrayield_047_distance_property_types_self_contained_repair_<timestamp>.txt
expected_shared_heartbeat: docs/chatgpt_status/_shared/heartbeat/single_multi_page_runner_heartbeat.txt

## Rule
Do not mark FINAL_READY until runner-produced smoke/raw/heartbeat evidence is present.
Do not open a separate runner. Existing shared runner should pick up the current-task or queue contract.
