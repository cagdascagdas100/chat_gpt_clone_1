# Distance Property Types - Progress Latest

page_key=distance_property_types
task_id=distance_property_types_bootstrap_20260703
run_started_at=2026-07-03T00:00:00Z
run_finished_at=2026-07-03T00:00:00Z
layer_name=Distance to Nearby Property Types
status=BLOCKED_INPUT_REQUIRED
completion_percent=8
final_ready=false

## Scope applied

- Six-category contract loaded: Industrial Unit, Detached Home, Retail Property, Apartment Building, Office Building, Mixed Building.
- Output schema prepared for CSV, GeoJSON, evidence manifest, latest progress report, and manual review CSV.
- Accuracy target preserved: accuracy_score_4 >= 3.0.
- No fake parcel/property rows were generated.
- changed_in_latest_run=true filter contract preserved for site integration.

## Counters

input_rows=0
processed_rows=0
verified_rows=0
manual_review_rows=0
accuracy_ge_3_rows=0
accuracy_lt_3_rows=0

## Outputs

geojson_output=F:\chatgpt\chat_gpt_clone_1_main\england_map_web\data\distance_property_types\distance_property_types_verified.geojson
csv_output=F:\chatgpt\chat_gpt_clone_1_main\england_map_web\data\distance_property_types\distance_property_types_verified.csv
manifest_output=F:\chatgpt\chat_gpt_clone_1_main\england_map_web\data\distance_property_types\distance_property_types_evidence_manifest.json
manual_review_output=F:\chatgpt\chat_gpt_clone_1_main\docs\chatgpt_status\distance_property_types\reports\distance_property_types_manual_review_latest.csv

## Safety flags

fake_data=false
db_write=false
ddl=false
migration_apply=false
prod_deploy=false

## Remaining blockers

- missing_verified_parcel_input_batch
- local_F_repo_runner_not_executed_from_this_chat
- live_pending_queue_copy_not_verifiable_from_this_chat
- official/web/map/photo evidence collection not yet run
- site layer/popup/right-panel/filter integration not yet verified

## Next batch

next_batch=Run the queued bootstrap task on the single shared runner. Then provide a real parcel source batch containing parcel_id, geometry or centroid, and candidate source/evidence fields. The runner must populate verified/manual-review rows only from real evidence.

## Next single action

next_single_action=Shared runner should execute docs/chatgpt_status/distance_property_types/automation/distance_property_types_batch_runner.ps1 and write its result to docs/chatgpt_status/distance_property_types/reports/distance_property_types_progress_latest.md.
