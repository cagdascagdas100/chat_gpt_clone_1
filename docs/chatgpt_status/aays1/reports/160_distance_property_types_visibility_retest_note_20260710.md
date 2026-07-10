# 160 Distance Property Types / Parcel Label visibility retest note

Branch: codex/aays-single-runner-v5-20260706
Runner: F:\TerraYield_AAYS_Portable\RUN_AAYS_STABLE_RUNNER_FROM_THIS_DISK.cmd

Retest summary:
- The requested CSV exists: england_map_web/data/distance_property_types/distance_property_types_verified.csv
- The CSV contains 6 real source-backed pilot seed rows.
- The two requested visibility JSON files were not found on the target branch.
- The requested 141 visibility report was not found on the target branch.

Files that must be present before candidate expansion continues:
- england_map_web/data/program_layer_matrix/distance_property_types_visible_rows_latest.json
- england_map_web/data/program_layer_matrix/distance_property_types_status_latest.json
- docs/chatgpt_status/distance_property_types/reports/141_distance_property_types_site_visibility_fix_report_20260710.md

Acceptance checks:
- Site shows the real 6 Parcel Label pilot rows row-by-row.
- Rows include source URL or source path, accuracy score, and changed marker.
- The 88 prepared bulk rows remain pending and are not counted as completed.
- final_ready remains false.
- fake_data, db_write, migration, and production_deploy remain false.
