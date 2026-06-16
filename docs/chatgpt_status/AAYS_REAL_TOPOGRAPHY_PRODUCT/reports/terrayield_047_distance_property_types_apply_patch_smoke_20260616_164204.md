# TerraYield 047 Distance Property Types self-contained repair report

timestamp: 20260616_164204
page_key: AAYS_REAL_TOPOGRAPHY_PRODUCT
branch: aays-runner-v17-icon-work-20260603-232706
status: PATCH_BLOCKED_NOT_FINAL_READY
completion_percent: 70
repo_root: F:\chatgpt\AAYS_WORKTREES\aays-runner-v17-icon-work-20260603-232706
base_url: http://127.0.0.1:8010
bbox: -0.55,51.28,0.35,51.75
limit: 10

## Patch notes
- wrote distance_property_types_overlay.js


## Patch errors
- missing map_layers.py at F:\chatgpt\AAYS_WORKTREES\aays-runner-v17-icon-work-20260603-232706\terrayield_land_intelligence\app\api\routes\map_layers.py
- missing index.html at F:\chatgpt\AAYS_WORKTREES\aays-runner-v17-icon-work-20260603-232706\england_map_web\index.html


## Static checks
- python py_compile map_layers.py: False
- node --check distance_property_types_overlay.js: True

## Endpoint smoke
URL: http://127.0.0.1:8010/map/distance-property-types?bbox=-0.55%2C51.28%2C0.35%2C51.75&limit=10
smoke_status: SMOKE_BLOCKED_APP_NOT_RUNNING_OR_ROUTE_NOT_REACHABLE
feature_count: 
missing_required_fields: 
missing_metric_value_fields: 

`json
Uzak sunucu hata döndürdü: (404) Bulunamadı.
`

## Events
`	ext
[2026-06-16T16:42:04.6265891+03:00] 047 self-contained repair started repo=F:\chatgpt\AAYS_WORKTREES\aays-runner-v17-icon-work-20260603-232706 branch=aays-runner-v17-icon-work-20260603-232706 page=AAYS_REAL_TOPOGRAPHY_PRODUCT
[2026-06-16T16:42:04.7885857+03:00] RUN git_fetch_branch
[2026-06-16T16:42:07.5179449+03:00] RUN git_pull_rebase_autostash
[2026-06-16T16:42:10.1660101+03:00] RUN node_check_overlay
[2026-06-16T16:42:10.4090114+03:00] RUN endpoint_smoke_distance_property_types
`

## Final rule
FINAL_READY requires parcel polygon FeatureCollection with at least one feature, all required popup/right-panel fields, and all six distance metric values populated. Empty FeatureCollection or null six-metric values are not feature-complete. No DB write/import/backfill was performed.