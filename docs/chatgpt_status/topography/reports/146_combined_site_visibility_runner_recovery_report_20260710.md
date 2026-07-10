# Topography / Height Difference - Combined Site Visibility and One-Click Runner Recovery Report

Repo: cagdascagdas100/chat_gpt_clone_1
Branch: codex/aays-single-runner-v5-20260706
Canonical root: F:\TerraYield_AAYS_Portable
Canonical launcher: F:\TerraYield_AAYS_Portable\RUN_AAYS_STABLE_RUNNER_FROM_THIS_DISK.cmd
Page key: topography / height_difference
Final: false

## User-visible failures

1. The 8012 Parcel Layer Matrix page does not show newly produced Topography work row-by-row.
2. The Topography current-changes panel is old/empty and does not expose source URL, local source path, report/proof path, accuracy, timestamp, calculation explanation, or blocker per parcel.
3. New work is not visually distinguished from old rows.
4. Real matrix coordinates exist for parcel_2757, parcel_2758, and parcel_2759, but the Topography coordinate export and latest_changes flow remain empty on the target branch.
5. The control panel previously showed a stale/closed runner. The actual process inspection later showed PID 15656 while the stale lock/GitHub proof still referenced PID 10108.
6. The runner can appear active without proving queue consumption, smoke-test file creation, GitHub push, and GitHub readback.

## Required site fix

Use the same F-portable data that powers:
127.0.0.1:8012/england_map_web/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html?refresh=portable

Topography must be selectable and must show row-level records. Each visible Topography record must include:
- parcel_id and parcel_ref
- hmlr_lat and hmlr_lon
- elevation_sea_level_m
- regional_average_elevation_m
- elevation_difference_regional_average_m
- source name
- source_url
- source_file_path or downloaded evidence path
- report/proof path
- source_date
- matching_method
- calculation_explanation
- confidence_percent
- accuracy_score_4
- needs_manual_review
- changed_in_latest_run
- change_reason
- generated_at
- final_ready=false
- fake_data=false

New rows must be visually distinct with a badge/class such as NEW_HEIGHT_DIFFERENCE and changed_in_latest_run=true. The current-changes panel must list the same rows, not only a summary object.

## Required coordinate fix

Read the real program-layer matrix/chunk source used by the 8012 page and export at least:
- parcel_2757: 51.6167362, -0.1421556
- parcel_2758: 51.6168592, -0.1417993
- parcel_2759: 51.6169525, -0.1430858

Write/update:
- docs/chatgpt_status/topography/handoff/topography_parcel_coordinate_handoff_20260710/topography_parcel_coordinate_export.csv
- docs/chatgpt_status/topography/handoff/topography_parcel_coordinate_handoff_20260710/topography_parcel_coordinate_export.geojson
- docs/chatgpt_status/topography/handoff/topography_parcel_coordinate_handoff_20260710/topography_starter_batch_candidates.json
- england_map_web/data/program_layer_matrix/topography_coordinate_handoff_latest.json
- docs/chatgpt_status/topography/status/140_site_visibility_matrix_coordinate_fix_latest.json
- outputs/england_program_parcel_matrix_20260629/topography_updates/latest_changes.json

Do not invent boundary geometry. Use geometry:null when no real boundary source is available.

## Required one-click runner fix

The control-panel button Tek Runner Baslat must perform all checks in one action without opening a second runner:

1. Detect the real running daemon process and command line.
2. Reconcile stale PID/lock records. The observed real process was PID 15656; stale proof referenced PID 10108.
3. Confirm the canonical F root, repo root, branch, and launcher.
4. Abort stale merge/rebase only when present.
5. Stash dirty local changes before pull and record the stash result.
6. Pull/sync the target branch.
7. Start exactly one runner only when no valid daemon exists.
8. Refresh heartbeat and lock with the real PID.
9. Scan the shared queue and process at least one harmless smoke-test task.
10. Create a small JSON proof file under docs/chatgpt_status/topography/runner_outputs/.
11. Commit and push that proof to the target branch.
12. Read the pushed file back from GitHub and record readback_ok=true.
13. Show PID, heartbeat, queue count, processed count, proof path, commit SHA, push status, and readback status in the panel.

Required smoke-test fields:
- AAYS_ONE_CLICK_SMOKE_TEST_OK=true only after GitHub readback succeeds
- runner_pid
- lock_pid
- heartbeat_at
- repo_root
- branch
- queue_detected_count
- processed_task_count
- proof_path
- commit_sha
- git_push_status
- github_readback_ok
- single_runner_only=true
- new_runner=false when an existing valid daemon is reused
- parallel_runner=false
- final_ready=false
- fake_data=false
- db_write=false
- migration=false
- production_deploy=false

## Height data integrity

After coordinate visibility and runner smoke-test both pass, continue only with real DEM/LiDAR/terrain evidence. Preferred evidence order:
1. Environment Agency / Defra LiDAR or terrain evidence
2. Ordnance Survey terrain evidence where licensed/available
3. Copernicus DEM
4. SRTM/USGS only as fallback

Do not write a height or height-difference value without real source evidence. Until sampling and calculation are complete, keep elevation fields null and mark needs_manual_review=true.

## Acceptance criteria

The fix is accepted only when all of the following are true:
- The control panel shows one real runner PID and fresh heartbeat.
- The lock PID equals the real daemon PID.
- processed_task_count increases above zero.
- A smoke-test JSON is committed, pushed, and readable from GitHub.
- The three starter parcels are present in CSV, GeoJSON, handoff JSON, and latest_changes.
- The 8012 Topography page shows the rows with source paths and a visible new-row marker.
- No fake height, fake completed state, fake 100 percent, or final_ready=true is written.

## Continuation rule

Only after the acceptance criteria above pass, continue the existing Topography task with source-backed DEM/LiDAR sampling and row-level website updates.
