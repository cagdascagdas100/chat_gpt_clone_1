# Runner task 047: run existing Distance Property Types automation artifact

Date: 2026-06-12
Priority: high
Mode: use existing checked-in automation artifact; no DB writes, migrations, imports, backfills, or index creation.

## Page and branch

- page_key: `AAYS_REAL_TOPOGRAPHY_PRODUCT`
- branch: `aays-runner-v17-icon-work-20260603-232706`
- expected local worktree: `F:\chatgpt\AAYS_WORKTREES\aays-runner-v17-icon-work-20260603-232706`

## Existing automation artifact

Use the already checked-in automation artifact:

`docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/automation/RUN_DISTANCE_047_SELF_CONTAINED_REPAIR.ps1`

## Goal

Produce fresh local evidence for the Distance to Nearby Property Types parcel popup layer.

Completion requires:

1. `/map/distance-property-types?bbox=west,south,east,north&limit=n` responds with a GeoJSON FeatureCollection.
2. Returned geometry is parcel polygon or multipolygon, not point-only assets.
3. Feature properties include the required parcel popup/right-panel fields named in the original 047 queue task.
4. Frontend binding for `distance_property_types_overlay.js` is present.
5. Static checks and smoke test evidence are recorded.
6. If source data is missing, write a data-blocked report and do not claim `FINAL_READY`.

## Expected outputs

Write fresh evidence under this page key only:

- `docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/reports/terrayield_047_distance_property_types_apply_patch_smoke_<timestamp>.md`
- `docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/status/terrayield_047_distance_property_types_status_<timestamp>.md`
- `docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/runner_outputs/terrayield_047_distance_property_types_self_contained_repair_<timestamp>.txt`

## Completion rule

Mark `FINAL_READY` only when the smoke report proves parcel polygons, required popup/right-panel fields, frontend binding, static checks, and Excel schema evidence. Otherwise report the exact blocker.