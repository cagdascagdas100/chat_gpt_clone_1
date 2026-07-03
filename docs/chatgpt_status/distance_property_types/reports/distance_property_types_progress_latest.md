# Distance Property Types - Progress Latest

page_key=distance_property_types
task_id=distance_property_types_bootstrap_20260703
run_started_at=2026-07-03T08:50:00Z
run_finished_at=2026-07-03T09:10:00Z
layer_name=Distance to Nearby Property Types
status=BLOCKED_INPUT_REQUIRED
completion_percent=15
final_ready=false
chatgpt_continue_mode=true
continue_command=devam et
blocker_issue=19

## Scope applied in this ChatGPT page

- Six-category contract loaded: Industrial Unit, Detached Home, Retail Property, Apartment Building, Office Building, Mixed Building.
- Output schema committed for CSV, GeoJSON, evidence manifest, latest progress report, and manual review CSV.
- Handoff docs committed for data contract, accuracy scale, runner workflow, site filter requirements, and manual review rules.
- ChatGPT continuation state committed for future `devam et` commands in this page.
- Accuracy target preserved: accuracy_score_4 >= 3.0.
- No fake parcel/property rows were generated.
- changed_in_latest_run=true filter contract preserved for site integration.
- GitHub main repo writes completed for non-executable bootstrap files.

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
- local_runner_not_executed_from_this_chat
- live_pending_queue_copy_not_verifiable_from_this_chat
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
- Blocker issue #19 created, labeled, and assigned.
- ChatGPT continuation state created so future `devam et` messages can resume from GitHub state.

## Continue behavior

When the user says `devam et`, ChatGPT must read the continuation state, latest progress report, queue task, and Issue #19 from GitHub main, then continue only with real repo evidence. If no new runner output or evidence batch exists, keep final_ready=false and update blockers. Never create fake parcel/property evidence.

## Next batch

next_batch=Run the queued bootstrap task on the single shared runner after placing the local runner file in F repo. Then process a real parcel source batch containing parcel_id, geometry or centroid, candidate source/evidence fields, distance fields, and official/web/map/photo evidence. The runner must populate verified/manual-review rows only from real evidence.

## Next single action

next_single_action=Place the local runner file in F repo, copy queue task to live pending queue, run the existing single shared runner, and return the real runner output report. Keep final_ready=false until evidence-backed data and site verification are complete.
