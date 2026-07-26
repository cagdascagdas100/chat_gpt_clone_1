# AAYS C Drive Folder Reconciliation - 2026-07-04

Updated at: 2026-07-04T14:57:32Z

## Scope

Marked C folders inspected:

- C:\Users\cagda\Documents\GitHub\AAYS
- C:\Users\cagda\Documents\GitHub\AAYS_gas_emissions_gas_emissions_shared_runner_contract_20260704
- C:\Users\cagda\Documents\GitHub\AAYS_gas_emissions_mainbase_20260703
- C:\Users\cagda\Documents\GitHub\chat_gpt_clone_1_security_pr_work_20260511_030446

Canonical F repo:

- F:\chatgpt\chat_gpt_clone_1_main

Targeted staging copy:

- F:\chatgpt\AAYS_C_DRIVE_IMPORT_STAGING_TARGETED_20260704

## What Was Copied To F Staging

The broad copy was stopped because it was too large. A targeted layer copy was then completed.

Copy manifest:

- F:\chatgpt\AAYS_C_DRIVE_IMPORT_STAGING_TARGETED_20260704\copy_manifest_20260704.json

Copy status summary:

- copied: 18
- missing_source: 13

Important copied staging buckets:

- c_aays docs for gas_emissions, security_public_safety, aays1, topography, internet_access
- c_aays program_layer_matrix data
- c_aays layer update outputs for gas_emissions, security_public_safety, topography, internet_access
- gas_emissions contract/mainbase docs and update outputs
- security_pr security_accuracy_expansion, ai-results, ai-task-scripts, ai-tasks

## Reconciliation Findings

Hash comparison against F main produced:

- total candidates: 1603
- missing in F main: 1556
- different from F main: 43
- already same: 4

Candidate CSV:

- docs/chatgpt_status/_shared/imports/c_drive_folder_reconciliation_candidates_20260704.csv

## Integrated Without Overwriting Existing Files

Only low-risk missing Gas Emissions and site-output files were copied into F main. Existing files were not overwritten.

Copied files:

- docs/chatgpt_status/gas_emissions/automation/aays_continue_runner_readme_20260703.md
- docs/chatgpt_status/gas_emissions/heartbeat/gas_emissions_single_runner_bridge_20260703_heartbeat.txt
- docs/chatgpt_status/gas_emissions/queue/aays_continue_runner_autonomous_request_20260704.json
- docs/chatgpt_status/gas_emissions/reports/gas_emissions_browser_smoke_20260703.json
- docs/chatgpt_status/gas_emissions/reports/gas_emissions_chunk_samples_20260703.json
- docs/chatgpt_status/gas_emissions/reports/gas_emissions_chunk_schema_paths_20260703.json
- docs/chatgpt_status/gas_emissions/status/aays_continue_runner_github_installed_20260704.txt
- docs/chatgpt_status/gas_emissions/heartbeat/gas_emissions_shared_runner_contract_20260704_heartbeat.txt
- docs/chatgpt_status/gas_emissions/reports/gas_emissions_shared_runner_contract_20260704_runner_output.txt
- docs/chatgpt_status/gas_emissions/status/gas_emissions_shared_runner_contract_20260704_completed.json
- docs/chatgpt_status/gas_emissions/status/gas_emissions_shared_runner_contract_20260704_gate.json
- docs/chatgpt_status/gas_emissions/status/gas_emissions_shared_runner_contract_20260704_started.json
- outputs/england_program_parcel_matrix_20260629/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html
- outputs/england_program_parcel_matrix_20260629/gas_emissions_runtime_patch_20260703.js

Skipped because already present:

- docs/chatgpt_status/gas_emissions/automation/aays_continue_runner_readme_20260703.md
- docs/chatgpt_status/gas_emissions/heartbeat/gas_emissions_single_runner_bridge_20260703_heartbeat.txt
- docs/chatgpt_status/gas_emissions/queue/aays_continue_runner_autonomous_request_20260704.json
- docs/chatgpt_status/gas_emissions/reports/gas_emissions_browser_smoke_20260703.json
- docs/chatgpt_status/gas_emissions/reports/gas_emissions_chunk_samples_20260703.json
- docs/chatgpt_status/gas_emissions/reports/gas_emissions_chunk_schema_paths_20260703.json
- docs/chatgpt_status/gas_emissions/status/aays_continue_runner_github_installed_20260704.txt

Integration CSV:

- docs/chatgpt_status/_shared/imports/c_drive_folder_integrated_low_risk_20260704.csv

## Not Auto-Integrated Yet

Security import archive was copied to F staging but not inserted into runtime/site paths automatically because it contains a large older evidence/runner expansion package. It should be consumed through a page-specific queue task that validates source dates, parcel IDs, confidence fields, and UI bindings.

Files with state=differs were not overwritten. They need manual or runner-based merge so recent main status is not replaced by older branch status.


## Active Queue Cleanup

Gas Emissions active queue was cleaned after import review. Historical queue files without the current shared-runner contract fields were moved to:

- docs/chatgpt_status/gas_emissions/import_candidates/queue_legacy_invalid_20260704/

This prevents old pending or blank-status queue records without llowed_paths from confusing the shared runner. The active queue now keeps only:

- docs/chatgpt_status/gas_emissions/queue/zzzzzzz_gas_emissions_current.task.json
## C To F Move Plan With Shortcuts

No C folder was moved or deleted in this run.

Safe future sequence:

1. Keep this F staging copy and current GitHub commit as the checkpoint.
2. Run app/site smoke on 8010 and 8020 after the low-risk import.
3. If smoke passes, create final F archive folders under F:\chatgpt\AAYS_C_DRIVE_ARCHIVE\.
4. Copy each marked C folder to its matching F archive folder with robocopy, excluding .git worktrees only if a Git clone already exists on F.
5. Verify file counts and selected hashes.
6. Rename each C folder to <name>_C_BACKUP_YYYYMMDD first. Do not delete immediately.
7. Create a directory junction at the old C path pointing to the F folder using New-Item -ItemType Junction.
8. Re-run 8010/8020 smoke and runner queue smoke.
9. Keep C backup until at least one successful runner cycle and site check passes.
10. Only after confirmed success should the C backup be removed.

## Rollback Plan

Current import rollback:

- before commit: unstage and remove files listed in c_drive_folder_rollback_manifest_20260704.json
- after commit: use git revert <commit_sha> from F:\chatgpt\chat_gpt_clone_1_main

Future C-to-F move rollback:

1. Stop any active local runner.
2. Remove the C junction only.
3. Rename <name>_C_BACKUP_YYYYMMDD back to the original folder name.
4. Keep the F archive copy for audit.
5. Run smoke again before continuing.

## Current Safety Result

- C originals were not moved.
- C originals were not deleted.
- Existing F main files were not overwritten.
- Low-risk missing Gas Emissions/site files were added.
- Security archive remains staged for later page-specific validation.
## Program Layer Matrix Integration - Continued

Additional missing parcel layer data files were integrated from C staging into F main after the first low-risk import.

Integrated runtime/data files:

- england_map_web/data/program_layer_matrix/distance_property_types.geojson
- england_map_web/data/program_layer_matrix/future_growth.geojson
- england_map_web/data/program_layer_matrix/gas_emissions.geojson
- england_map_web/data/program_layer_matrix/internet.geojson
- england_map_web/data/program_layer_matrix/manifest.json
- england_map_web/data/program_layer_matrix/planned_buildings.geojson
- england_map_web/data/program_layer_matrix/security.geojson
- england_map_web/data/program_layer_matrix/topography.geojson

Topography note: F main had a 480 byte placeholder with 0 features. It was backed up under docs/chatgpt_status/_shared/imports/replaced_placeholders_20260704/ and replaced with the C staging version containing 77970 features.

Validation file:

- docs/chatgpt_status/_shared/imports/program_layer_matrix_validation_20260704.json

Feature counts validated:

- distance_property_types.geojson: 92283 features, bytes=94075297
- future_growth.geojson: 0 features, bytes=572
- gas_emissions.geojson: 3533 features, bytes=2711733
- internet.geojson: 33785 features, bytes=24704099
- manifest.json: 0 features, bytes=1981
- planned_buildings.geojson: 47 features, bytes=179990
- security.geojson: 92283 features, bytes=61369763
- topography.geojson: 77970 features, bytes=61981121

Additional update outputs copied without overwriting existing latest_changes conflicts:

- outputs/england_program_parcel_matrix_20260629/gas_emissions_updates/README_TR.md
- outputs/england_program_parcel_matrix_20260629/internet_access_updates/latest_changes.json
- outputs/england_program_parcel_matrix_20260629/internet_access_updates/README_TR.md
- outputs/england_program_parcel_matrix_20260629/security_public_safety_updates/README_TR.md
- outputs/england_program_parcel_matrix_20260629/topography_updates/README_TR.md

Smoke checks:

- 8010 /health: HTTP 200
- 8010 /england_map_web/: HTTP 200
- 8010 program_layer_matrix gas_emissions/internet/security/topography/manifest: HTTP 200
- 8020 matrix page: HTTP 200 and contains Gas Emissions, Security, Internet, Topography tokens
- 8020 internet_access latest_changes: HTTP 200
- 8020 gas_emissions runtime patch: HTTP 200

C drive move status: not moved yet. The data/app integration phase now has a Git rollback point before physical junction work.
