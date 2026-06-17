# QUEUE TASK — Distance Property Types Page 3.4

task_id: distance_property_types_page34_task_20260617_001
page_key: AAYS_REAL_TOPOGRAPHY_PRODUCT
branch: main
status: queued
priority: high
single_runner_only: true
FINAL_READY: false
completion_percent: 20

## Automation Script
`docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/automation/aays_distance_property_types_finalizer_20260617_page34.ps1`

## Runner Instruction
Execute exactly this page-key task with the existing shared runner. Do not spawn a second runner. Produce reports only under `docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/`.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/automation/aays_distance_property_types_finalizer_20260617_page34.ps1" -PageKey "AAYS_REAL_TOPOGRAPHY_PRODUCT" -PreferredWorktreeRoot "F:\chatgpt\AAYS_WORK\distance_property_types_20260617_clean"
```

## Required Work
1. Detect this page-key runner contract by reading reports/status/heartbeat/current-task/control/queue/runner_tasks/automation/runner_outputs and `_shared` if present.
2. Select F clean worktree first, D clean worktree second.
3. Copy only the three C reference integration files into the D/F target when available:
   - `england_map_web/app.js`
   - `terrayield_land_intelligence/app/api/routes/map_layers.py`
   - `terrayield_land_intelligence/run_uvicorn_8010.ps1`
4. Run static checks.
5. Start/verify PostGIS on expected DB port 55460.
6. Start/verify API on 8010.
7. Probe `/health` and `/map/distance-property-types`.
8. Run UI smoke without installing unrelated dependencies; if UI smoke cannot run, report blocker.
9. Commit/push reports/status/heartbeat/runner_outputs back to GitHub.

## Final Gate
Only mark `FINAL_READY: true` and `completion_percent: 100` when live runtime + data + UI smoke evidence are present in GitHub reports.
