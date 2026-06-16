# AAYS 7.3 Nearby Planned Developments runtime backend patch

PAGE_KEY: AAYS_REAL_TOPOGRAPHY_PRODUCT
TASK: pb_runtime_backend_patch
LAYER: Nearby Planned Developments
BRANCH: aays-runner-v17-icon-work-20260603-232706
STATUS: BACKEND_PATCH_APPLIED_NEEDS_LOCAL_RUNTIME_SMOKE
FINAL_READY: false

## Evidence read before patch

- `docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/reports/pb_final_smoke_20260616T160852.txt` contained `FINAL_READY: True`, but only static marker/icon checks.
- `docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/status/pb_final_smoke_20260616T160852.txt` contained `FINAL_READY: True`, but no ROOT_200 / PLANNED_SEARCH_200 / PLANNED_PARCEL_LAYER_200 / UI acceptance fields.
- Uploaded handoff states runtime had `/` = 200 and `/england_map_web/` = 200, but `/planned-assets/search` and `/planned-assets/parcel-layer` were 404.

## Changed files

- `terrayield_land_intelligence/app/main.py`
  - Replaced hard route imports with fail-soft module registration so one broken route/config import does not prevent app startup.
- `terrayield_land_intelligence/app/services/planned_asset_response.py`
  - Fixed package import from `terrayield_land_intelligence.app...` to `app...` for local uvicorn runtime.
- `terrayield_land_intelligence/app/api/routes/planned_assets.py`
  - Added `/planned-assets/search` route.
  - Kept `/planned-assets/parcel-layer` route returning a real empty FeatureCollection with explicit data-gap metadata.
- `terrayield_land_intelligence/app/core/config.py`
  - Added minimal fail-soft `get_settings()` so route registration is not blocked by config import side effects.

## Acceptance status

ROOT_200: unknown_local_runtime_required
WEB_200: unknown_local_runtime_required
PLANNED_SEARCH_200: unknown_local_runtime_required
PLANNED_PARCEL_LAYER_200: unknown_local_runtime_required
UI_PLANNED_LAYER_ACCEPTED: false
DATA_PRESENT: false

FINAL_STATUS: ROUTE_PATCHED_NEEDS_RUNTIME_SMOKE

## Next operator step

Run the F worktree runtime smoke against `http://127.0.0.1:8010/`, `/planned-assets/search?limit=1`, and `/planned-assets/parcel-layer?bbox=-0.2,51.4,0.2,51.7&limit=10`; then perform browser UI smoke for the planned button/layer/popup.
