# Distance Property Types - Progress Latest

page_key=distance_property_types
task_id=distance_property_types_automation_expand_20260703_1000
run_finished_at=2026-07-03T10:00:00Z
layer_name=Distance to Nearby Property Types
status=MULTI_TASK_EXPANDED_WAITING_FOR_OUTPUT
completion_percent=18
final_ready=false
chatgpt_continue_mode=true
continue_command=devam et
blocker_issue=19
single_runner_pickup_requested=true

## Latest automation cycle

- Prior queued task reports were searched.
- No committed worker/probe report found yet.
- No committed evidence discovery report found yet.
- No committed site check report found yet.
- Added output collector task.
- Added blocker narrowdown task.
- Added evidence input CSV template.
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
- evidence collection not yet run
- site verification not yet complete
- executable local worker file still not proven in the active local repo

## Continue behavior

When the user says `devam et`, read queue tasks, latest progress, Issue #19, input template, and any committed outputs. Process only real evidence and update repo reports.

## Next action

next_single_action=Existing single worker should process queued tasks or a real evidence batch should be committed using the template. Then say `devam et` in this page.
