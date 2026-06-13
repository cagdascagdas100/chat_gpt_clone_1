# AAYS_REAL_TOPOGRAPHY_PRODUCT — Final Topography Patch + Smoke Request

PAGE_KEY=AAYS_REAL_TOPOGRAPHY_PRODUCT
BRANCH=aays-runner-v17-icon-work-20260603-232706
STATUS=FINAL_PATCH_SMOKE_REQUESTED

## Context
Manual queue execution and source inventory reached product progress estimate 88. Remaining work is final app patch verification and runtime/smoke evidence, not DB import, migration, fake data generation, or deployment.

## Required constraints
- Do not create fake data.
- Do not write to DB.
- Do not run migrations.
- Do not deploy.
- Preserve existing single runner/bridge/queue infrastructure.
- Use only this page key, branch, repo, and status/report folders.
- Keep 8099 tile overlay lifecycle separate from 8765 parcel lookup lifecycle.
- 8099 tile failure must not block 8765 parcel lookup evidence.

## Required final verification
Verify current branch app code and produce a report proving selected parcel topography panel/popup includes or can render:
- center_elevation_m
- region_average_elevation_m
- elevation_difference_from_region_average_m
- source/source_dataset/topography_source
- source_date/calculated_at
- confidence_level/confidence_reason
- matching_method
- calculation_explanation
- layer_name
- parcel_id
- parcel_ref/inspire_id
- elevation_above_sea_level_m
- region_scope_type
- region_scope_value
- region_sample_count
- class_level or elevation_difference_class
- color_category or color_hex
- datum
- source_resolution_m

## Required smoke evidence
Write a report at:

docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/reports/topography_final_patch_smoke_20260613_istanbul.txt

Report must include:
- PAGE_KEY
- BRANCH
- RUN_AT
- APP_JS_PATH
- NODE_CHECK_APP_JS result
- 8765 lookup smoke result or explicit reason unavailable
- UI/popup field rendering evidence
- HAS_region_average_elevation_m
- HAS_elevation_difference_from_region_average_m
- HAS_hight_differance_icon
- FAKE_DATA_CREATED=False
- DB_WRITE=False
- MIGRATION=False
- DEPLOY=False
- FINAL_READY=True or FINAL_READY=False with exact blockers
- PRODUCT_PROGRESS_ESTIMATE

## Success condition
If all required fields and smoke evidence are present, set FINAL_READY=True and PRODUCT_PROGRESS_ESTIMATE=100.
