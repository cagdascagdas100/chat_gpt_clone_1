# Distance Property Types - Missing Script Path Identified

page_key=distance_property_types
check_time_local=2026-07-03T21:20:00
status=MISSING_SCRIPT_PATH_IDENTIFIED
final_ready=false

## User-provided failed task details

Bootstrap failed with missing script path:
F:\chatgpt\chat_gpt_clone_1_main\docs\chatgpt_status\distance_property_types\automation\distance_property_types_batch_runner.ps1

Other distance_property_types task files failed because they did not include an executable script_path field.

## Required fix

Create the local script at the bootstrap script_path, then requeue only distance_property_types tasks with script_path pointing to that script.

## Safety flags

fake_data=false
db_write=false
ddl=false
migration=false
production_deploy=false
