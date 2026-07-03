# Distance Property Types - Progress Latest

page_key=distance_property_types
task_id=distance_property_types_missing_script_20260703_2110
run_finished_at=2026-07-03T21:10:00
status=BRIDGE_TASKS_FAILED_MISSING_SCRIPT
completion_percent=22
final_ready=false
chatgpt_continue_mode=true
continue_command=devam et
latest_bridge_failure_report=docs/chatgpt_status/distance_property_types/reports/bridge_failed_missing_script_20260703_2110.md
latest_runner_fix_report=docs/chatgpt_status/distance_property_types/runner_outputs/fix_runner_git_sync_20260703_203814.report.json

## Current verified state

- Portable queue runner is active.
- Queue files were copied to bridge pending.
- Bridge processed the tasks and moved them to failed.
- Failure class is missing script / unresolved executable script.
- Do not start a second runner.

## Failed distance_property_types task family

- bootstrap
- worker probe
- evidence discovery
- site check
- output collector
- blocker narrowdown

## Narrowed blocker

bridge_runner_requires_task_script_path_or_existing_script

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

## Next action

Create or map the executable local script expected by the failed task files, then requeue only distance_property_types tasks. Keep final_ready=false until real output is produced.
