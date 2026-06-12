# 047 runner contract inventory

timestamp: 20260612_165634
page_key: AAYS_REAL_TOPOGRAPHY_PRODUCT
branch: aays-runner-v17-icon-work-20260603-232706
status: RUNNER_OUTPUT_MISSING
completion_percent: 62
powershell_reason: GitHub queue/current-task exists but no expected runner smoke report was visible from ChatGPT.

## Expected report pattern

terrayield_047_distance_property_types_apply_patch_smoke_*.md

## Expected reports found



## Folder inventory

## docs\chatgpt_status\AAYS_REAL_TOPOGRAPHY_PRODUCT\control
MISSING

## docs\chatgpt_status\AAYS_REAL_TOPOGRAPHY_PRODUCT\queue
MISSING

## docs\chatgpt_status\AAYS_REAL_TOPOGRAPHY_PRODUCT\current-task
MISSING

## docs\chatgpt_status\AAYS_REAL_TOPOGRAPHY_PRODUCT\runner_tasks
MISSING

## docs\chatgpt_status\AAYS_REAL_TOPOGRAPHY_PRODUCT\automation
MISSING

## docs\chatgpt_status\AAYS_REAL_TOPOGRAPHY_PRODUCT\reports
- local_current_task_pinned_20260611_013011.txt | 2026-06-11 01:30:13 | 189 bytes
- local_current_task_pinned_20260611_012831.txt | 2026-06-11 01:28:34 | 189 bytes

## docs\chatgpt_status\AAYS_REAL_TOPOGRAPHY_PRODUCT\status
- chatgpt_progress_100_functional_final_ready_20260611_172451.txt | 2026-06-11 17:24:51 | 471 bytes
- local_single_runner_pin_applied_20260611_150704.txt | 2026-06-11 15:07:07 | 454 bytes
- local_pin_started_20260611_125107.txt | 2026-06-11 12:51:11 | 469 bytes
- local_pin_started_20260611_122955.txt | 2026-06-11 12:30:01 | 476 bytes

## docs\chatgpt_status\AAYS_REAL_TOPOGRAPHY_PRODUCT\heartbeat


## Next action

If RUNNER_OUTPUT_MISSING, the single runner/poller is not consuming the visible 047 queue/current-task files or writes output elsewhere. Check runner polling contract and configure it to consume:
- docs\chatgpt_status\AAYS_REAL_TOPOGRAPHY_PRODUCT\queue\terrayield_047_distance_property_types_apply_patch_smoke_20260612_1328.md
- docs\chatgpt_status\AAYS_REAL_TOPOGRAPHY_PRODUCT\current-task\terrayield_047_distance_property_types_apply_patch_smoke_20260612_1328.md

No DB write, migration, import, or backfill was performed by this diagnostic.
