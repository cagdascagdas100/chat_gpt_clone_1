# Current task: 047 Distance Property Types run existing automation

Date: 2026-06-12
Page key: `AAYS_REAL_TOPOGRAPHY_PRODUCT`
Branch: `aays-runner-v17-icon-work-20260603-232706`
Status: `QUEUED_FOR_SINGLE_LOCAL_RUNNER`

This current-task pointer supersedes the earlier handoff-only queue entry and points the local runner to the existing checked-in automation task.

Active queue task:
`docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/queue/terrayield_047_distance_property_types_run_existing_automation_20260612.md`

Automation artifact referenced by that queue task:
`docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/automation/RUN_DISTANCE_047_SELF_CONTAINED_REPAIR.ps1`

Expected evidence outputs:
- `docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/reports/terrayield_047_distance_property_types_apply_patch_smoke_<timestamp>.md`
- `docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/status/terrayield_047_distance_property_types_status_<timestamp>.md`
- `docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/runner_outputs/terrayield_047_distance_property_types_self_contained_repair_<timestamp>.txt`

Completion rule: mark `FINAL_READY` only when the smoke report proves parcel polygons, required popup/right-panel fields, frontend binding, static checks, and Excel schema evidence. If runtime data or service availability blocks this, write the exact blocker and do not claim `FINAL_READY`.
