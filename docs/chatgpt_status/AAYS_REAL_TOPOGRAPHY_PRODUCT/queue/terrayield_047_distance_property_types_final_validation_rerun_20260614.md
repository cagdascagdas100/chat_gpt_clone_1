# Runner task 047 final validation rerun

page_key: `AAYS_REAL_TOPOGRAPHY_PRODUCT`
branch: `aays-runner-v17-icon-work-20260603-232706`
mode: shared-single-runner
priority: high

Use page-local automation artifact:
`docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/automation/RUN_DISTANCE_047_SELF_CONTAINED_REPAIR.ps1`

Expected evidence outputs under this page key:
- `docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/reports/terrayield_047_distance_property_types_apply_patch_smoke_<timestamp>.md`
- `docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/status/terrayield_047_distance_property_types_status_<timestamp>.md`
- `docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/runner_outputs/terrayield_047_distance_property_types_self_contained_repair_<timestamp>.txt`

Completion rule: do not claim FINAL_READY unless this page's report proves acceptance criteria. If blocked, write exact blocker in this page's reports/status folders.
