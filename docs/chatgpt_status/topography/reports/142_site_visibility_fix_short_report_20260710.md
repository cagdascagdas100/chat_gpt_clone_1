# Topography Height Difference Site Visibility Fix

Status: fix required
Final: false

The current matrix page does not show Topography Height Difference work as row-level visible records. The user must see each processed parcel with its coordinate source, evidence file path, accuracy, pending blocker, and new-row marker.

Screenshot findings:
- The matrix table already shows real coordinate fields.
- Visible fields include parcel_id, hmlr_inspire_id, hmlr_lat, hmlr_lon, and hmlr_geometry_accuracy.
- Starter rows visible in the table are parcel_2757, parcel_2758, and parcel_2759.
- Topography current changes panel still shows only old summary JSON and no visible row-level results.

Required fix:
1. Use hmlr_lat and hmlr_lon from the same matrix data that feeds the page.
2. Write at least three Topography coordinate records for parcel_2757, parcel_2758, and parcel_2759.
3. Update Topography latest_changes so the page can show a row-level list.
4. Each row must include parcel_id, parcel_ref, centroid_lat, centroid_lon, coordinate_status, coordinate_source_path, source name, source file path, matching_method, calculation_explanation, accuracy_score_4, needs_manual_review, blocker, changed_in_latest_run, final_ready, and fake_data.
5. New rows must have changed_in_latest_run=true and a visible badge such as NEW_HEIGHT_DIFFERENCE.
6. Height fields must stay null until real terrain evidence is sampled.
7. Do not invent elevation, boundary geometry, source paths, or final status.

Required files to update:
- docs/chatgpt_status/topography/handoff/topography_parcel_coordinate_handoff_20260710/topography_parcel_coordinate_export.csv
- docs/chatgpt_status/topography/handoff/topography_parcel_coordinate_handoff_20260710/topography_parcel_coordinate_export.geojson
- england_map_web/data/program_layer_matrix/topography_coordinate_handoff_latest.json
- docs/chatgpt_status/topography/status/140_site_visibility_matrix_coordinate_fix_latest.json
- outputs/england_program_parcel_matrix_20260629/topography_updates/latest_changes.json

Acceptance criteria:
- The page shows at least three Topography row-level records.
- The visible rows include parcel_2757, parcel_2758, and parcel_2759.
- Each visible row shows source path and evidence path.
- New rows are visually marked.
- No fake height value is written.
- final_ready remains false.
