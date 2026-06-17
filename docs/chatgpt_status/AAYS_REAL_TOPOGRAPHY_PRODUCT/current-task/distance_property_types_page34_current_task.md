# CURRENT TASK — AAYS Page 3.4 Distance Property Types

page_key: AAYS_REAL_TOPOGRAPHY_PRODUCT
branch: main
status: QUEUED_FOR_SINGLE_SHARED_RUNNER
FINAL_READY: false
completion_percent: 35
created_at: 2026-06-17T00:00:00+03:00

## Task
Run the existing single shared runner contract for this page key and execute the automation script below. Do not start a second runner. Do not use another page key. Do not move or replace C runner/bridge infrastructure.

## Automation Script Path
`docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/automation/aays_distance_property_types_finalizer_20260617_page34.ps1`

## Required Command For Runner
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/automation/aays_distance_property_types_finalizer_20260617_page34.ps1" -PageKey "AAYS_REAL_TOPOGRAPHY_PRODUCT" -PreferredWorktreeRoot "F:\chatgpt\AAYS_WORK\distance_property_types_20260617_clean"
```

## Acceptance Gate
Do not mark final unless GitHub reports contain all of these:

- `status: FINAL_READY` or `FINAL_READY: true`
- `/health` returned HTTP 200 and database ok
- `/map/distance-property-types?bbox=-0.55,51.28,0.35,51.75&limit=10` returned HTTP 200
- `parcel_count_visible > 0`
- popup contract ok
- right panel contract ok
- UI click/network smoke for `parcel_label` or Distance to Nearby Property Types is proven

## Expected Reports
- `docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/reports/distance_property_types_df_worktree_apply_report_*.md`
- `docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/reports/distance_property_types_df_worktree_smoke_report_*.md`
- `docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/reports/distance_property_types_df_worktree_blockers_*.md`
- `docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/status/distance_property_types_status_*.md`

## Non-Collision Rule
This task may run static file checks, DB/API probes, and UI smoke in one automation script. It must not create unrelated tasks and must not concurrently modify the same source files from multiple jobs.
