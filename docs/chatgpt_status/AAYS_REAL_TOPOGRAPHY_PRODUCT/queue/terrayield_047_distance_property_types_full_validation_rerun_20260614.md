# Runner task 047: full validation rerun through shared single runner

Date: 2026-06-14
Priority: high
Page key: `AAYS_REAL_TOPOGRAPHY_PRODUCT`
Branch: `aays-runner-v17-icon-work-20260603-232706`
Runner contract: shared single runner scans this page key queue/current-task and executes only page-local automation scripts.

## Automation artifact

`docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/automation/RUN_DISTANCE_047_SELF_CONTAINED_REPAIR.ps1`

## Required work

Run the existing self-contained 047 automation from the F-disk worktree. Produce fresh evidence under this same page key only.

## Acceptance checks

The run must verify or explicitly block each item:

1. Backend route `/map/distance-property-types` exists and returns GeoJSON FeatureCollection for bbox smoke.
2. Geometry is parcel polygon or multipolygon, not point-only asset output.
3. Required popup/right-panel fields are present or exact missing fields are reported.
4. Frontend overlay `distance_property_types_overlay.js` exists and is bound in `england_map_web/index.html`.
5. Static checks are recorded.
6. Excel/schema evidence for the 047 output contract is recorded or blocker is written.
7. Source data / service availability blocker is written if endpoint cannot prove FINAL_READY.

## Expected outputs

- `docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/reports/terrayield_047_distance_property_types_apply_patch_smoke_<timestamp>.md`
- `docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/status/terrayield_047_distance_property_types_status_<timestamp>.md`
- `docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/runner_outputs/terrayield_047_distance_property_types_self_contained_repair_<timestamp>.txt`

## Completion rule

Do not claim `FINAL_READY` unless the report proves parcel polygons, required popup/right-panel fields, frontend binding, static checks, and schema evidence. Otherwise write the exact blocker and completion percentage.