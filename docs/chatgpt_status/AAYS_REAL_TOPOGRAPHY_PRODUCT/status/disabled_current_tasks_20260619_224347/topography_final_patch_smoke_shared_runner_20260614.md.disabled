# AAYS_REAL_TOPOGRAPHY_PRODUCT — Shared Runner Task

PAGE_KEY: AAYS_REAL_TOPOGRAPHY_PRODUCT
BRANCH: aays-runner-v17-icon-work-20260603-232706
STATUS: QUEUED_FOR_SHARED_RUNNER

## Automation script

Run this page-owned automation script from the repository worktree root:

`docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/automation/topography_final_patch_smoke_20260614.ps1`

## Constraints

- Do not open a separate runner or PowerShell.
- Use the existing single shared runner only.
- Do not create fake data.
- Do not write to DB.
- Do not run migrations.
- Do not deploy.
- Preserve 8099 tile overlay lifecycle and 8765 parcel lookup lifecycle separation.

## Expected report

The script must write and push a report under:

`docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/reports/topography_final_patch_smoke_<timestamp>.txt`

The report must include:

- `STATUS=PATCH_SMOKE_READY_FOR_UI_LOOKUP_PROOF` or an explicit failure status.
- `PRODUCT_PROGRESS_ESTIMATE=94` when patch smoke succeeds.
- evidence lines for:
  - `HAS_region_average_elevation_m=True`
  - `HAS_elevation_difference_from_region_average_m=True`
  - `HAS_calculation_explanation=True`
  - `HAS_hight_differance_icon=True`
  - `HAS_normalizeTopographyLookupForPopup=True`
  - `HAS_buildTopographyPopupRowsHtml=True`
  - node syntax check output.

## Next gate

After this report appears, the next task is UI/lookup runtime proof and FINAL_READY gating.