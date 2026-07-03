# Distance Property Types - Progress Latest

page_key=distance_property_types
task_id=distance_property_types_multi_task_queue_20260703_0950
run_finished_at=2026-07-03T09:50:00Z
layer_name=Distance to Nearby Property Types
status=MULTI_TASK_QUEUED_WAITING_FOR_OUTPUT
completion_percent=17
final_ready=false
chatgpt_continue_mode=true
continue_command=devam et
blocker_issue=19
single_runner_pickup_requested=true

## Newly queued parallel tasks

- docs/chatgpt_status/distance_property_types/queue/distance_property_types_probe_worker_20260703_0950.task.json
- docs/chatgpt_status/distance_property_types/queue/distance_property_types_find_evidence_batch_20260703_0950.task.json
- docs/chatgpt_status/distance_property_types/queue/distance_property_types_site_check_20260703_0950.task.json

## Current state

- current_task.json remains READY_FOR_SINGLE_RUNNER_PICKUP.
- Existing single worker must be used.
- New worker must not be opened.
- No committed runner output found yet.
- No committed evidence batch found yet.
- No fake parcel/property rows were generated.

## Counters

input_rows=0
processed_rows=0
verified_rows=0
manual_review_rows=0
accuracy_ge_3_rows=0
accuracy_lt_3_rows=0

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

## Continue behavior

When the user says `devam et`, read current_task, continuation_state, queue tasks, Issue #19, latest progress, and any committed output. Process only real evidence. Keep final_ready=false until real runner/evidence/site proof exists.

## Next action

next_single_action=Wait for the existing single worker to commit any of the expected reports, then say `devam et` in this page.
