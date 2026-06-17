# CONTROL — Distance Property Types Page 3.4 Runner Pickup

page_key: AAYS_REAL_TOPOGRAPHY_PRODUCT
branch: main
status: PICKUP_CONTROL_WRITTEN
FINAL_READY: false
completion_percent: 40
control_id: distance_property_types_page34_runner_pickup_control_20260617_002
created_at: 2026-06-17T00:00:00+03:00
single_runner_only: true

## Purpose
The page-key task exists in `current-task`, `queue`, and `runner_tasks`, but no runner heartbeat or runner output has been observed yet. This control file is a non-product, single-runner-safe pickup request. It does not create a second runner and does not change the product scope.

## Required Runner Action
The existing shared runner must execute exactly this script from the repository root:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/automation/aays_distance_property_types_finalizer_20260617_page34.ps1" -PageKey "AAYS_REAL_TOPOGRAPHY_PRODUCT" -PreferredWorktreeRoot "F:\chatgpt\AAYS_WORK\distance_property_types_20260617_clean"
```

## Expected Evidence Files
- `docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/reports/distance_property_types_df_worktree_apply_report_*.md`
- `docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/reports/distance_property_types_df_worktree_smoke_report_*.md`
- `docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/reports/distance_property_types_df_worktree_blockers_*.md`
- `docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/status/distance_property_types_status_*.md`
- `docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/heartbeat/distance_property_types_heartbeat_*.md`
- `docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/runner_outputs/distance_property_types_runner_output_*.txt`

## Non-Collision Rules
- Do not start a separate runner.
- Do not write outside `docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/` for task evidence.
- Do not create unrelated tasks.
- Do not run parallel child jobs that modify the same files, database, or API process.
- Static checks, DB/API probe, and UI smoke may run inside the same automation script because they produce separate evidence files and do not conflict with one another.

## Final Gate
Only mark `FINAL_READY: true` and `completion_percent: 100` when GitHub reports prove: health database ok, distance endpoint HTTP 200 with non-empty features, popup/right-panel contract ok, and UI click/network smoke.