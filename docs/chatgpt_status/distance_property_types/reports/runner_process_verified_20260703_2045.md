# Distance Property Types - Runner Process Verified

page_key=distance_property_types
check_time_local=2026-07-03T20:45:00
status=RUNNER_PROCESS_SEEN_LOCAL
final_ready=false

## User-provided local process proof

- Process name: powershell.exe
- ProcessId: 4704
- Command: F:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-task-scripts\portable_queue_runner.ps1

## Interpretation

A queue runner process is running. Do not start a second runner. Remaining issue is local git push race / non-fast-forward after rebase, plus waiting for runner output reports.

## Safety flags

fake_data=false
db_write=false
ddl=false
migration=false
production_deploy=false
