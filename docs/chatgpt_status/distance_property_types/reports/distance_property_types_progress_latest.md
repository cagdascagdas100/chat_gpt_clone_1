# Distance Property Types - Progress Latest

page_key=distance_property_types
task_id=distance_property_types_script_path_fixed_requeued_20260703_2130
run_finished_at=2026-07-03T21:30:00
status=SCRIPT_PATH_CREATED_TASKS_REQUEUED_WAITING_FOR_RUNNER_OUTPUT
completion_percent=23
final_ready=false
chatgpt_continue_mode=true
continue_command=devam et
latest_bridge_failure_report=docs/chatgpt_status/distance_property_types/reports/bridge_failed_missing_script_20260703_2110.md
latest_missing_script_report=docs/chatgpt_status/distance_property_types/reports/missing_script_path_identified_20260703_2120.md

## Current verified state

- Missing executable script path was identified.
- Local script was created at docs/chatgpt_status/distance_property_types/automation/distance_property_types_batch_runner.ps1.
- Test-Path returned true for the local script.
- Six distance_property_types failed tasks were requeued to the bridge pending folder with script_path added.
- Portable queue runner should remain open.
- New runner output is not visible in GitHub yet.

## Requeued task family

- bootstrap
- worker probe
- evidence discovery
- site check
- output collector
- blocker narrowdown

## Narrowed blocker

waiting_for_requeued_tasks_to_publish_runner_output

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

On the next `devam et`, read runner_outputs and ai-results output paths. Keep final_ready=false until real evidence-backed rows exist.
