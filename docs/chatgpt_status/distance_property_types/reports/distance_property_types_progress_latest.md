# Distance Property Types - Progress Latest

page_key=distance_property_types
task_id=distance_property_types_runner_pickup_20260703_0918
run_started_at=2026-07-03T08:50:00Z
run_finished_at=2026-07-03T09:18:00Z
layer_name=Distance to Nearby Property Types
status=SINGLE_RUNNER_PICKUP_REQUESTED
completion_percent=16
final_ready=false
chatgpt_continue_mode=true
continue_command=devam et
blocker_issue=19
single_runner_pickup_requested=true
current_task=docs/chatgpt_status/distance_property_types/current_task.json
pickup_request=docs/chatgpt_status/distance_property_types/runner_control/PICKUP_REQUEST_20260703_0918.md

## Scope applied in this ChatGPT page

- Six-category contract loaded: Industrial Unit, Detached Home, Retail Property, Apartment Building, Office Building, Mixed Building.
- Output schema committed for CSV, GeoJSON, evidence manifest, latest progress report, and manual review CSV.
- Handoff docs committed for data contract, accuracy scale, runner workflow, site filter requirements, and manual review rules.
- ChatGPT continuation state committed for future `devam et` commands in this page.
- Current task and pickup request committed for single shared runner pickup.
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
queue_task=F:\chatgpt\chat_gpt_clone_1_main\docs\chatgpt_status\distance_property_types\queue\distance_property_types_bootstrap_20260703.task.json
site_requirements=F:\chatgpt\chat_gpt_clone_1_main\docs\chatgpt_status\distance_property_types\site_integration\distance_property_types_site_requirements.md
continuation_state=F:\chatgpt\chat_gpt_clone_1_main\docs\chatgpt_status\distance_property_types\state\chatgpt_continuation_state.json
continuation_rules=F:\chatgpt\chat_gpt_clone_1_main\docs\chatgpt_status\distance_property_types\state\CHATGPT_CONTINUE_RULES_TR.md

## Safety flags

fake_data=false
db_write=false
ddl=false
migration_apply=false
prod_deploy=false

## Remaining blockers

- missing_verified_parcel_input_batch
- no_committed_runner_output_seen_yet
- local_runner_execution_not_proven_yet
- live_pending_queue_copy_not_verified_yet
- official/web/map/photo evidence collection not yet run
- site layer/popup/right-panel/filter integration not yet verified
- executable runner file must be created in the local F repo outside this ChatGPT GitHub write path

## This page completed

- Repo queue task created.
- Parseable empty GeoJSON created.
- Header-only verified CSV created.
- Evidence manifest created.
- Manual review CSV header created.
- Handoff/control docs created.
- Site integration checklist created.
- Runner notes created.
- Blocker issue #19 created, labeled, assigned, and commented.
- ChatGPT continuation state created so future `devam et` messages can resume from GitHub state.
- Current task created for single runner pickup.
- Pickup request created for the shared worker flow.

## Continue behavior

When the user says `devam et`, ChatGPT must read current_task, continuation state, latest progress report, queue task, Issue #19, and any committed runner outputs from GitHub main. If new real runner output or evidence exists, process it. If no new output exists, keep final_ready=false and update blockers. Never create fake parcel/property evidence.

## Next batch

next_batch=Existing single shared runner should pick up the distance_property_types queue task. If no evidence batch exists, runner should write a blocker output rather than fake results. Then ChatGPT can continue from committed output on the next `devam et`.

## Next single action

next_single_action=Wait for real committed runner output or evidence batch in the repo, then say `devam et` in this page. ChatGPT will read GitHub state and continue from there.
