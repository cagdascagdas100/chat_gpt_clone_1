# Distance Property Types - Progress Latest

page_key=distance_property_types
task_id=distance_property_types_bootstrap_20260703
run_started_at=2026-07-09T19:03:54.8852365Z
run_finished_at=2026-07-09T19:03:55.2288939Z
layer_name=Distance to Nearby Property Types
status=BLOCKED_INPUT_REQUIRED
completion_percent=45
final_ready=false
product_final_ready=false

## Counters

input_rows=6
processed_rows=6
verified_rows=6
manual_review_rows=0
accuracy_ge_3_rows=6
accuracy_lt_3_rows=0

## Outputs

geojson_output=F:\TerraYield_AAYS_Portable\runner_system\AAYS_WT\AAYS_STABLE_RUNNER_WORKTREES\distance_property_types_dpt_geometry_join_pr\england_map_web\data\distance_property_types\distance_property_types_verified.geojson
csv_output=F:\TerraYield_AAYS_Portable\runner_system\AAYS_WT\AAYS_STABLE_RUNNER_WORKTREES\distance_property_types_dpt_geometry_join_pr\england_map_web\data\distance_property_types\distance_property_types_verified.csv
manifest_output=F:\TerraYield_AAYS_Portable\runner_system\AAYS_WT\AAYS_STABLE_RUNNER_WORKTREES\distance_property_types_dpt_geometry_join_pr\england_map_web\data\distance_property_types\distance_property_types_evidence_manifest.json
manual_review_output=F:\TerraYield_AAYS_Portable\runner_system\AAYS_WT\AAYS_STABLE_RUNNER_WORKTREES\distance_property_types_dpt_geometry_join_pr\docs\chatgpt_status\distance_property_types\reports\distance_property_types_manual_review_latest.csv

## Safety flags

fake_data=false
db_write=false
ddl=false
migration_apply=false
prod_deploy=false

## Remaining blockers

- geojson_geometry_generation_requires_source_geometry_or_existing_feature_collection
- site_integration_not_verified_with_real_features

## Next batch

next_batch=Provide or generate a real source batch with parcel_id, geometry/centroid, candidate property type, distance fields, and official/web/map/photo evidence. Rows below 3.0/4 or with conflict must remain in manual review.

## Next single action

next_single_action=Run evidence-backed source batch through this script, then verify GeoJSON rendering and the Guncel degisiklikler filter in the local site.