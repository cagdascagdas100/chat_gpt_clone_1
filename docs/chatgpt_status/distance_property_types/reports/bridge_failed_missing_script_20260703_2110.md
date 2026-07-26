# Distance Property Types - Bridge Failed Missing Script

page_key=distance_property_types
check_time_local=2026-07-03T21:10:00
status=BRIDGE_TASKS_FAILED_MISSING_SCRIPT
final_ready=false

## User-provided bridge evidence

The portable queue runner is active, but distance_property_types tasks were moved to the bridge failed folder.

Observed failed items include:
- distance_property_types_site_check_20260703_0950.runner_error.txt
- distance_property_types_probe_worker_20260703_0950.runner_error.txt
- distance_property_types_find_evidence_batch_20260703_0950.runner_error.txt
- distance_property_types_collect_outputs_20260703_1000.runner_error.txt
- distance_property_types_bootstrap_20260703.runner_error.txt
- distance_property_types_blocker_narrowdown_20260703_1000.runner_error.txt
- matching task.failed_missing_script.task.json files

## Narrowed blocker

bridge_runner_requires_task_script_path_or_existing_script. The runner is running, but the queued tasks do not resolve to executable scripts.

## Safety flags

fake_data=false
db_write=false
ddl=false
migration=false
production_deploy=false
