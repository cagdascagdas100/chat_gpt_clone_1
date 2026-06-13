# AAYS_REAL_TOPOGRAPHY_PRODUCT — final patch + smoke task

PAGE_KEY: AAYS_REAL_TOPOGRAPHY_PRODUCT
BRANCH: aays-runner-v17-icon-work-20260603-232706
MODE: TOPOGRAPHY_FINAL_PATCH_SMOKE
SAFETY: no fake data, no DB writes, no migrations, no deploy.

## Current state
- Manual queue execution proved runner queue item can run.
- Real topography source inventory exists and reports PRODUCT_PROGRESS_ESTIMATE=88.
- Remaining work is final product patch verification plus smoke/FINAL_READY evidence.

## Required work
1. Use only this repo/branch/page key.
2. Inspect current app.js in the active branch before editing.
3. Ensure selected parcel popup/panel topography output displays:
   - center_elevation_m / elevation_above_sea_level_m
   - region_average_elevation_m
   - elevation_difference_from_region_average_m
   - source/source_dataset/topography_source
   - source_date/calculated_at
   - confidence_level/confidence_reason
   - matching_method
   - calculation_explanation when available
4. Preserve 8099 tile overlay lifecycle and 8765 parcel lookup lifecycle separation.
5. Do not change database, migrations, import data, or deploy.
6. Run static syntax check and any available safe smoke that proves 8765 lookup/topography popup path includes region average and difference fields.

## Required report
Write:
`docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/reports/topography_final_patch_smoke_20260614.txt`

Report must include at minimum:
- PAGE_KEY
- BRANCH
- APP_JS_PATH
- PATCH_APPLIED true/false
- NODE_CHECK_APP_JS pass/fail
- HAS_region_average_elevation_m true/false
- HAS_elevation_difference_from_region_average_m true/false
- HAS_source_fields true/false
- HAS_confidence_fields true/false
- HAS_matching_method true/false
- LOOKUP_8765_SMOKE pass/fail/not_available
- UI_POPUP_SMOKE pass/fail/not_available
- FAKE_DATA_CREATED=False
- DB_WRITE=False
- MIGRATION=False
- DEPLOY=False
- FINAL_READY true/false
- PRODUCT_PROGRESS_ESTIMATE
