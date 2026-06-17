# RUNNER TASK MIRROR — Distance Property Types Page 3.4

task_id: distance_property_types_page34_task_20260617_001
page_key: AAYS_REAL_TOPOGRAPHY_PRODUCT
branch: main
status: queued
single_runner_only: true
script_path: docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/automation/aays_distance_property_types_finalizer_20260617_page34.ps1

## Execute
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/automation/aays_distance_property_types_finalizer_20260617_page34.ps1" -PageKey "AAYS_REAL_TOPOGRAPHY_PRODUCT" -PreferredWorktreeRoot "F:\chatgpt\AAYS_WORK\distance_property_types_20260617_clean"
```

## Output Contract
The runner must write and push these GitHub evidence files:

- `docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/reports/distance_property_types_df_worktree_apply_report_*.md`
- `docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/reports/distance_property_types_df_worktree_smoke_report_*.md`
- `docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/reports/distance_property_types_df_worktree_blockers_*.md`
- `docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/status/distance_property_types_status_*.md`
- `docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/heartbeat/distance_property_types_heartbeat_*.md`
- `docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/runner_outputs/distance_property_types_runner_output_*.txt`

## Stop Condition
Stop only when status is `FINAL_READY` or blockers are explicitly listed in the blocker report.
