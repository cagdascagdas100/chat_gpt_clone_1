# 047 Distance Property Types blocker report

page_key: AAYS_REAL_TOPOGRAPHY_PRODUCT
branch: aays-runner-v17-icon-work-20260603-232706
status: BLOCKED_NOT_FINAL_READY
completion_percent: 74

## Finding

The current page-local automation artifact is present and queue-triggered:

`docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/automation/RUN_DISTANCE_047_SELF_CONTAINED_REPAIR.ps1`

The current route/popup patch includes the required output field names, but the implementation populates only these source distances from `parcel_context_summary`:

- nearest_industrial_unit_m
- nearest_retail_property_m
- nearest_office_building_m

The following required metrics are still emitted as null placeholders:

- nearest_detached_home_m
- nearest_apartment_building_m
- nearest_mixed_building_program_m

Therefore the layer cannot be marked FINAL_READY even if the endpoint returns polygons, because the acceptance contract requires all 6 distance-to-property-type metrics in the parcel popup/right panel.

## Required next task

Update the page-local automation/patch so the endpoint derives or joins all 6 required property-type distance metrics from available cached context tables, preferring read-only sources such as:

- parcel_context_metric_details
- parcel_context_summary
- parcel_scenario_scores
- parcel_use6, if present

No DB writes or migrations are approved. Empty source data must be reported as DATA_BLOCKED, not FINAL_READY.

## Expected final evidence

The runner must write a new report:

`docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/reports/terrayield_047_distance_property_types_apply_patch_smoke_<timestamp>.md`

That report must prove:

- endpoint returns parcel polygons, or explicitly reports source-data blocker;
- popup/right-panel exposes all 6 distance fields;
- static frontend/backend checks ran;
- route is bound under `/map/distance-property-types`;
- FINAL_READY is used only when all acceptance criteria are met.
