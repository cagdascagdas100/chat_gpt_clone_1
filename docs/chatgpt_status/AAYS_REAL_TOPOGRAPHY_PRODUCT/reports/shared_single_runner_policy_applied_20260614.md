# Shared single runner policy applied

Page key: `AAYS_REAL_TOPOGRAPHY_PRODUCT`
Branch: `aays-runner-v17-icon-work-20260603-232706`
Date: 2026-06-14
Status: `SHARED_SINGLE_RUNNER_POLICY_APPLIED_NOT_FINAL_READY`

## Decision

Other AAYS pages must not open independent PowerShell windows, page-local runners, or scheduled tasks.

Each page must write its own task into its own page key folder:

- `docs/chatgpt_status/<PAGE_KEY>/queue/`
- `docs/chatgpt_status/<PAGE_KEY>/current-task/`

Each task must reference only its own page-local automation artifact:

- `docs/chatgpt_status/<PAGE_KEY>/automation/<SCRIPT>.ps1`

The shared multi-page runner is the only intended runner process:

- `docs/chatgpt_status/_shared/automation/RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER.ps1`

The shared runner scans `docs/chatgpt_status/<PAGE_KEY>/queue` and `docs/chatgpt_status/<PAGE_KEY>/current-task` across page keys and executes one page-local automation task at a time.

## Constraint

A shared runner heartbeat has not yet been observed in GitHub at:

- `docs/chatgpt_status/_shared/heartbeat/single_multi_page_runner_heartbeat.txt`

So the policy is installed, but runtime confirmation is still pending.

## Current page continuation

For this page, the active Distance Property Types task remains:

- `docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/current-task/terrayield_047_distance_property_types_parcel_popup_20260612.md`
- `docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/queue/terrayield_047_distance_property_types_run_existing_automation_20260612.md`

Expected evidence remains:

- `docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/reports/terrayield_047_distance_property_types_apply_patch_smoke_<timestamp>.md`
- `docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/status/terrayield_047_distance_property_types_status_<timestamp>.md`
- `docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/runner_outputs/terrayield_047_distance_property_types_self_contained_repair_<timestamp>.txt`

## Completion rule

This page cannot be marked `FINAL_READY` until its own smoke report proves parcel polygons, required popup/right-panel fields, frontend binding, static checks, and Excel schema evidence.
