# TerraYield 047 Distance Property Types self-contained repair report

timestamp: 20260616_222800
page_key: AAYS_REAL_TOPOGRAPHY_PRODUCT
branch: aays-runner-v17-icon-work-20260603-232706
status: CONTRACT_BLOCKED_NOT_FINAL_READY
completion_percent: 82
repo_root: F:\chatgpt\AAYS_WORKTREES\aays-runner-v17-icon-work-20260603-232706
base_url: http://127.0.0.1:8010
bbox: -0.55,51.28,0.35,51.75
limit: 10

## Patch notes
- distance-property-types route already present but marker not replaced
- wrote distance_property_types_overlay.js
- index.html already references overlay


## Patch errors
- none


## Static checks
- python py_compile map_layers.py: True
- node --check distance_property_types_overlay.js: True

## Endpoint smoke
URL: http://127.0.0.1:8010/map/distance-property-types?bbox=-0.55%2C51.28%2C0.35%2C51.75&limit=10
smoke_status: CONTRACT_BLOCKED_NOT_FINAL_READY
feature_count: 1
missing_required_fields: layer_name, parcel_ref, use6_label, overall_distance_property_type_score_pct, class_level, source_name, evidence_summary, accuracy_scale, matching_method, nearest_industrial_unit_m, nearest_detached_home_m, nearest_retail_property_m, nearest_apartment_building_m, nearest_office_building_m, nearest_mixed_building_program_m
missing_metric_value_fields: nearest_industrial_unit_m, nearest_detached_home_m, nearest_retail_property_m, nearest_apartment_building_m, nearest_office_building_m, nearest_mixed_building_program_m

`json
{"type":"FeatureCollection","features":[{"type":"Feature","geometry":{"type":"Polygon","coordinates":[[[-0.10900000000000004,51.5103],[-0.09100000000000003,51.5103],[-0.09100000000000003,51.5197],[-0.10900000000000004,51.5197],[-0.10900000000000004,51.5103]]]},"properties":{"parcel_id":"047_SMOKE_PARCEL","ref":"047_SMOKE_PARCEL","inspire_id":"047_SMOKE_PARCEL","score":70,"percentage":70,"class":"C_PARTIAL","level":"C_PARTIAL","color_category":"C_PARTIAL","yapi_turu_ve_6_renk":"C_PARTIAL","kaynak_ve_belirleme_yontemi":"standalone_047_smoke_api","dogruluk_skalasi":"C_PARTIAL","evidence":"Standalone smoke endpoint for 047 route contract verification.","source_date":"2026-06-16","accuracy":"C_PARTIAL","confidence":"C_PARTIAL","match_method":"standalone_047_smoke_api","calculation_explanation":"Non-null smoke values for all six nearby property type distance metrics.","raw_fields":{"source":"standalone_047_smoke_api","bbox":"-0.55,51.28,0.35,51.75","limit":10},"distance_to_nearest_industrial_unit_m":125.0,"distance_to_nearest_detached_home_m":80.0,"distance_to_nearest_retail_property_m":210.0,"distance_to_nearest_apartment_building_m":95.0,"distance_to_nearest_office_building_m":260.0,"distance_to_nearest_mixed_building_program_m":180.0}}],"metadata":{"layer":"Distance to Nearby Property Types","bbox":"-0.55,51.28,0.35,51.75","limit":10,"mode":"standalone_047_smoke_api"}}
`

## Events
`	ext
[2026-06-16T22:28:00.8592746+03:00] 047 self-contained repair started repo=F:\chatgpt\AAYS_WORKTREES\aays-runner-v17-icon-work-20260603-232706 branch=aays-runner-v17-icon-work-20260603-232706 page=AAYS_REAL_TOPOGRAPHY_PRODUCT
[2026-06-16T22:28:02.7437975+03:00] RUN git_fetch_branch
[2026-06-16T22:28:13.7508900+03:00] RUN git_pull_rebase_autostash
[2026-06-16T22:28:22.5512405+03:00] RUN python_py_compile_map_layers
[2026-06-16T22:28:25.5270357+03:00] RUN node_check_overlay
[2026-06-16T22:28:25.7907400+03:00] RUN endpoint_smoke_distance_property_types
`

## Final rule
FINAL_READY requires parcel polygon FeatureCollection with at least one feature, all required popup/right-panel fields, and all six distance metric values populated. Empty FeatureCollection or null six-metric values are not feature-complete. No DB write/import/backfill was performed.