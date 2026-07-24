# AAYS1 Ready To Sell Geometry Review - Local Visibility Blocker

Date: 2026-07-10
Page key: aays1
Branch: codex/aays-single-runner-v5-20260706

## User visible problem

The local browser page at port 8012 still shows stale and unreadable content. The screenshot shows:

- AI result count shown on page: 14
- Visible progress shown on page: 70 percent
- Header and Turkish labels are mojibake, for example broken forms of Satir, Fotograf Kaniti, Dogruluk, Yeni Guven
- New evidence is not shown as a distinct latest-run block or badge
- Row-level source, status, report, and local artifact paths are not visible
- The page does not expose which data file was actually loaded by the browser

## Repository evidence currently expected

The repository data file `england_map_web/data/geometry_review_3of4/photo_ai_boundary_review_results.json` currently reports:

- rows_total: 1264
- rows_reviewed: 30
- rows_with_candidate_photo_urls: 30
- rows_pending_vision_download: 30
- rows_with_live_source_verified: 30
- site_visible_progress_percent: 86
- final_ready: false
- fake_data: false
- db_write: false
- migration: false
- production_deploy: false

This means the local page is not showing the latest expected site data.

## Repository HTML problem

The current HTML still loads:

- DATA = `../docs/chatgpt_status/aays1/geometry_review_3of4/all_1264_real_geometry_3of4.geojson`
- AI = `data/geometry_review_3of4/photo_ai_boundary_review_results.json`

But the user asked to validate these local site data paths:

- `england_map_web/data/geometry_review_3of4/all_1264_real_geometry_3of4.geojson`
- `england_map_web/data/geometry_review_3of4/photo_ai_boundary_review_results.json`
- `england_map_web/data/aays1/aays1_product_status_latest.json`

The page must make the actual loaded paths visible on screen and use cache-busting on every fetch.

## Required Codex fix

Update `england_map_web/geometry_review_3of4_columns_1264.html` and any related local loader/server config so the page does all of this:

1. Keep UTF-8 clean in browser rendering.
2. Load the geometry file from `data/geometry_review_3of4/all_1264_real_geometry_3of4.geojson` relative to `england_map_web/`.
3. Load AI evidence from `data/geometry_review_3of4/photo_ai_boundary_review_results.json`.
4. Load product status from `data/aays1/aays1_product_status_latest.json`.
5. Add cache-busting, for example `?refresh=` plus timestamp or URL refresh token, to all JSON and GeoJSON fetches.
6. Show a top diagnostics panel with:
   - loaded geometry path
   - loaded AI evidence path
   - loaded product status path
   - HTTP/fetch status for each file
   - AI status
   - product status
   - rows_reviewed
   - rows_with_live_source_verified
   - site_visible_progress_percent
   - product completion percent
   - final_ready
   - fake_data, db_write, migration, production_deploy
7. Show a clear STALE LOCAL DATA warning when loaded values do not match the expected latest evidence. For now expected latest evidence is 30 reviewed, 30 live source verified, 86 percent visible progress.
8. For each row show:
   - row_id
   - listing_url
   - parcel_ref
   - source_verification_status
   - source_verification_result
   - source_listing_type_verified
   - source_photo_count_verified
   - source_area_verified
   - source_planning_ref_verified
   - source_page_title_verified
   - confidence_after
   - visual_match_score
   - photo_shape_type
   - geometry_mismatch_flag
   - status/report path if available
   - downloaded photo/local artifact path if available, otherwise explicit `not downloaded`
   - latest-run marker if available
9. Visually mark rows added or changed in the latest run with badges:
   - NEW IN LATEST RUN
   - LIVE SOURCE VERIFIED
   - VISION PENDING
   - NOT 3.5 PLUS
10. Do not write 3.5+ confidence unless photo download, polygon render, and vision compare are all present.
11. Do not change final_ready to true.
12. Do not alter fake_data, db_write, migration, or production_deploy safety flags.

## Acceptance criteria

The fix is accepted only if:

- The local page opened at `http://127.0.0.1:8012/england_map_web/geometry_review_3of4_columns_1264.html?refresh=codexfix` shows clean Turkish text.
- It shows the loaded file paths.
- It shows 30 reviewed rows, 30 live-source verified rows, and 86 percent visible progress when the latest repo data is loaded.
- Rows 1 through 30 are visible with row-level source evidence.
- New/latest-run rows are visually distinguished.
- Missing local artifacts are shown explicitly as `not downloaded` or `vision pending`.
- No fake 3.5+ confidence is introduced.
- final_ready remains false.

## After fix

After this visibility problem is fixed, continue the existing verification task from row 30 onward. Do not increase progress unless a real pushed status/output file exists.