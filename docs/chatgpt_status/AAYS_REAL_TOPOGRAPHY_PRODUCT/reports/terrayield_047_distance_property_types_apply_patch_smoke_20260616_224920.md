# TerraYield 047 Distance Property Types self-contained repair report

timestamp: 20260616_224920
page_key: AAYS_REAL_TOPOGRAPHY_PRODUCT
branch: aays-runner-v17-icon-work-20260603-232706
status: SMOKE_BLOCKED_APP_NOT_RUNNING_OR_ROUTE_NOT_REACHABLE
completion_percent: 78
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
smoke_status: SMOKE_BLOCKED_APP_NOT_RUNNING_OR_ROUTE_NOT_REACHABLE
feature_count: 
missing_required_fields: 
missing_metric_value_fields: 

`json
Uzak sunucuya bağlanılamıyor
`

## Events
`	ext
[2026-06-16T22:49:20.6496658+03:00] 047 self-contained repair started repo=F:\chatgpt\AAYS_WORKTREES\aays-runner-v17-icon-work-20260603-232706 branch=aays-runner-v17-icon-work-20260603-232706 page=AAYS_REAL_TOPOGRAPHY_PRODUCT
[2026-06-16T22:49:21.2277741+03:00] RUN git_fetch_branch
[2026-06-16T22:49:22.8886843+03:00] RUN git_pull_rebase_autostash
[2026-06-16T22:49:26.9687843+03:00] RUN python_py_compile_map_layers
[2026-06-16T22:49:27.5964523+03:00] RUN node_check_overlay
[2026-06-16T22:49:28.0279519+03:00] RUN endpoint_smoke_distance_property_types
`

## Final rule
FINAL_READY requires parcel polygon FeatureCollection with at least one feature, all required popup/right-panel fields, and all six distance metric values populated. Empty FeatureCollection or null six-metric values are not feature-complete. No DB write/import/backfill was performed.