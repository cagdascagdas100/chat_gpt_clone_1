# Distance Property Types - Progress Latest

page_key=distance_property_types
task_id=distance_property_types_run_source_seed_20260708
run_started_at=2026-07-08T15:45:00Z
run_finished_at=2026-07-08T15:45:00Z
layer_name=Distance to Nearby Property Types
status=INPUT_READY_WAITING_SINGLE_RUNNER_VALIDATION
completion_percent=62
final_ready=false
product_final_ready=false

## Counters

input_rows=6
processed_rows=0
verified_rows=0
manual_review_rows=0
accuracy_ge_3_rows=6
accuracy_lt_3_rows=0

## Outputs

source_input=docs/chatgpt_status/distance_property_types/inputs/distance_property_types_source_candidates.csv
queued_task=docs/chatgpt_status/distance_property_types/queue/0002_distance_property_types_run_source_seed_20260708.task.json
csv_output=england_map_web/data/distance_property_types/distance_property_types_verified.csv
geojson_output=england_map_web/data/distance_property_types/distance_property_types_verified.geojson
manual_review_output=docs/chatgpt_status/distance_property_types/reports/distance_property_types_manual_review_latest.csv

## Safety flags

fake_data=false
db_write=false
ddl=false
migration_apply=false
prod_deploy=false

## Resolved blockers

- source_candidate_csv_is_header_only
- missing_real_evidence_rows_at_input_stage

## Remaining blockers

- waiting_single_runner_validation_output
- geometry_distance_join_required_before_final
- site_integration_not_verified_with_real_features

## Next batch

next_batch=Single runner must validate the 6 source-backed candidate rows, then join geometry/distance evidence before any final_ready claim.

## Next single action

next_single_action=Run queued task distance_property_types_run_source_seed_20260708 through the single shared runner and verify site 8020 changed-status panel.
