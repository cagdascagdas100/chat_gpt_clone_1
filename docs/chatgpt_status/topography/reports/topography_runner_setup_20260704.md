# Topography Runner Setup 2026-07-04

setup_completed=true
repo_root=F:\chatgpt\chat_gpt_clone_1_main
branch=main
single_runner_lock=AAYS_TOPOGRAPHY_SINGLE_RUNNER_20260704
fake_data_created=false
final_ready=false
blockers=verified_rows_missing
filled_parcel_count=0
accuracy_score_4=0/4
browser_smoke_overall_ok=true
site_8020_latest_changes_synced=true

## Installed files

- docs/chatgpt_status/topography/automation/START_TOPOGRAPHY_AUTOFIX_FROM_ANYWHERE_20260704.ps1
- docs/chatgpt_status/topography/automation/topography_single_runner_bridge_20260703.ps1
- docs/chatgpt_status/topography/prompts/topography_chatgpt_continue_prompt_20260704.md
- docs/chatgpt_status/topography/current_task/topography_current_task_20260703.json
- docs/chatgpt_status/topography/browser_smoke/topography_browser_smoke_latest_20260704.json
- docs/chatgpt_status/topography/heartbeat/topography_single_runner_heartbeat_latest_20260704.json
- docs/chatgpt_status/topography/heartbeat/topography_bridge_heartbeat_latest_20260704.json
- docs/chatgpt_status/topography/runner_state/topography_single_runner_state_20260704.json
- docs/chatgpt_status/topography/logs/topography_autofix_latest_20260704.log
- outputs/england_program_parcel_matrix_20260629/topography_updates/latest_changes.json

## Continue command

`powershell
$u="https://raw.githubusercontent.com/cagdascagdas100/chat_gpt_clone_1/main/docs/chatgpt_status/topography/automation/START_TOPOGRAPHY_AUTOFIX_FROM_ANYWHERE_20260704.ps1"; $p="$env:TEMP\START_TOPOGRAPHY_AUTOFIX_FROM_ANYWHERE_20260704.ps1"; Invoke-WebRequest -UseBasicParsing $u -OutFile $p; powershell -NoProfile -ExecutionPolicy Bypass -File $p
`

## Current status

`	ext
Topography devam durumu:
Tamamlanan: %25
Kalan: %75
Bekleme: 0 dakika
Doldurulan parsel: 0
Dogruluk: 0/4
Program entegrasyonu: %25
Web sitesi guncellemesi: %25
final_ready: false
blocker: verified_rows_missing
next_action: continue with the existing single shared runner until verified rows, UI smoke and site visibility are complete
`

## Remaining blocker

erified_rows_missing: no official/evidence-backed Topography parcel rows are present in docs/chatgpt_status/topography/fixtures/topography_verified_rows_template_20260703.csv. The runner is ready, but final_ready must remain false until real verified rows are added and matched into GeoJSON/UI output.