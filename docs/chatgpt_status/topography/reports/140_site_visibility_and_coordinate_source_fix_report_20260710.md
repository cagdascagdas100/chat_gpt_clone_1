# Topography 140 - Site Visibility and Coordinate Source Fix Report

Page key: topography
Layer: Topography / Height Difference
Branch: codex/aays-single-runner-v5-20260706
Canonical runner: F:\TerraYield_AAYS_Portable\RUN_AAYS_STABLE_RUNNER_FROM_THIS_DISK.cmd
Final: false

## User-visible problem
The user cannot see the new Topography / Height Difference work row-by-row on the local site.
The visible site is:

127.0.0.1:8012/england_map_web/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html?refresh=portable

The site shows the layer matrix table, but the Topography current-changes panel is still empty/old and does not expose verified row-level Topography results with source paths.

## Screenshot findings
The screenshot proves that real parcel coordinate fields are already available in the local matrix table. Example visible columns:

- matrix_record
- row_no
- parcel_id
- hmlr_row_id
- hmlr_inspire_id
- london_authority
- hmlr_area_m2
- hmlr_lat
- hmlr_lon
- hmlr_geometry_accuracy
- use6_class_color
- use6_accuracy

Visible sample rows include:

- parcel_2757, hmlr_inspire_id 52213412, Barnet, hmlr_lat 51.6167362, hmlr_lon -0.1421556, hmlr_geometry_accuracy 4/4
- parcel_2758, hmlr_inspire_id 52213916, Barnet, hmlr_lat 51.6168592, hmlr_lon -0.1417993, hmlr_geometry_accuracy 4/4
- parcel_2759, hmlr_inspire_id 52040420, Barnet, hmlr_lat 51.6169525, hmlr_lon -0.1430858

This means the previous blocker 'no parcel coordinates' is not accurate for the local 8012 matrix page. The correct coordinate source is the program layer matrix data used by the local page, not only england_map_web/data/program_layer_matrix/topography.geojson.

## Root causes to fix
1. Runner scans only Topography-specific empty files and misses the matrix rows that already contain hmlr_lat/hmlr_lon.
2. Topography current changes file remains empty:
   outputs/england_program_parcel_matrix_20260629/topography_updates/latest_changes.json
3. The 8012 site has a Topography current-changes panel but receives no row-level Topography change objects.
4. New Topography work is not visually distinguished in the matrix table.
5. The site currently displays Gas Emissions in the selected layer dropdown; Topography results must be visible when the Topography layer is selected and also in the Topography current-changes panel.

## Required fix for Jodex/Codex
Use the real local matrix data that powers the 8012 page as the canonical coordinate source. Do not rely only on topography.geojson.

Search/read these local/generated sources in the F portable repo:

- outputs/england_program_parcel_matrix_20260629/chunks/manifest.json
- outputs/england_program_parcel_matrix_20260629/chunks/filter_indexes.json
- outputs/england_program_parcel_matrix_20260629/chunks/page_*.json
- outputs/england_program_parcel_matrix_20260629/**/*.json
- england_map_web/data/**/*.json
- england_map_web/data/**/*.geojson

Extract at minimum:

- matrix_record
- row_no
- parcel_id
- hmlr_row_id
- hmlr_inspire_id
- london_authority
- hmlr_area_m2
- hmlr_lat
- hmlr_lon
- hmlr_geometry_accuracy

Map these to Topography coordinate export fields:

- parcel_id = parcel_id
- parcel_ref = hmlr_inspire_id if a better parcel_ref is not present
- centroid_lat = hmlr_lat
- centroid_lon = hmlr_lon
- geometry_type = null if boundary is not available
- geometry = null if boundary is not available
- coordinate_source_path = actual local matrix/chunk file path
- geometry_source_path = null unless a real boundary file exists
- coordinate_status = verified_from_matrix_hmlr_lat_lon
- final_ready = false
- fake_data = false

## Required output files
Write/update:

1. docs/chatgpt_status/topography/handoff/topography_parcel_coordinate_handoff_20260710/topography_parcel_coordinate_export.csv
2. docs/chatgpt_status/topography/handoff/topography_parcel_coordinate_handoff_20260710/topography_parcel_coordinate_export.geojson
3. docs/chatgpt_status/topography/handoff/topography_parcel_coordinate_handoff_20260710/topography_starter_batch_candidates.json
4. docs/chatgpt_status/topography/status/138_find_canonical_parcel_coordinates_latest.json
5. outputs/england_program_parcel_matrix_20260629/topography_updates/latest_changes.json

## Site-visible latest_changes format
Topography latest_changes.json must include row-level objects visible on the 8012 site. Each object should include at minimum:

- changed_in_latest_run: true
- change_reason: Topography starter height-difference row created from matrix HMLR coordinate source
- matrix_record
- row_no
- parcel_id
- parcel_ref
- hmlr_row_id
- hmlr_inspire_id
- london_authority
- centroid_lat
- centroid_lon
- coordinate_source_path
- geometry_source_path
- geometry: null if no real boundary
- elevation_sea_level_m: null until real DEM/LIDAR sampling is completed
- regional_average_elevation_m: null until real regional calculation is completed
- elevation_difference_regional_average_m: null until real calculation is completed
- source
- source_url
- source_file_path
- source_date
- matching_method
- calculation_explanation
- confidence_percent
- accuracy_score_4
- needs_manual_review

## New-row visual requirement
Make new Topography records visibly distinguishable in the site. Recommended approach:

- add changed_in_latest_run=true in latest_changes objects
- add change_reason text
- ensure the current-changes panel lists those rows
- if table rendering supports it, add a CSS class or badge for Topography rows, e.g. NEW_TOPOGRAPHY_HEIGHT_DIFFERENCE

## Data integrity rules
- Do not invent coordinates.
- Use hmlr_lat/hmlr_lon only when read from the real matrix data file.
- Do not invent boundary geometry.
- If no boundary exists, write geometry:null.
- Do not invent elevation values.
- Elevation must only be written after real DEM/LIDAR/terrain source evidence is available.
- Keep final_ready=false.
- Keep fake_data=false, db_write=false, migration=false, production_deploy=false.

## Acceptance criteria
- At least 3 Topography starter candidates are exported from real matrix rows.
- The 8012 site Topography current-changes panel shows these rows with parcel_id, coordinate, source path and changed_in_latest_run=true.
- The matrix table can show new Topography row status or badge.
- 138 status output exists and records the number of exported rows.
- No fake elevation is written.

## Next action after this fix
After coordinate export is visible on the site, continue with official DEM/LIDAR/terrain source sampling for the same starter parcels and then update latest_changes.json with source-backed height difference values.
