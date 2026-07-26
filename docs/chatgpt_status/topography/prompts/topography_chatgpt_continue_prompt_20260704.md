# Topography ChatGPT Continue Prompt - 2026-07-04

Layer: Topography
Page key: topography
Repo: cagdascagdas100/chat_gpt_clone_1
Branch: main
Local runner repo root: F:\chatgpt\chat_gpt_clone_1_main

When the user writes only "devam", continue with the single runner flow below. Do not create fake parcel rows, fake evidence, fake browser smoke, or fake final_ready.

## First command for ChatGPT local runner

```powershell
$u="https://raw.githubusercontent.com/cagdascagdas100/chat_gpt_clone_1/main/docs/chatgpt_status/topography/automation/START_TOPOGRAPHY_AUTOFIX_FROM_ANYWHERE_20260704.ps1"; $p="$env:TEMP\START_TOPOGRAPHY_AUTOFIX_FROM_ANYWHERE_20260704.ps1"; Invoke-WebRequest -UseBasicParsing $u -OutFile $p; powershell -NoProfile -ExecutionPolicy Bypass -File $p
```

## Required behavior

1. Use only `F:\chatgpt\chat_gpt_clone_1_main` as the repo root.
2. Respect the single runner lock. If a runner is already active, do not start a duplicate.
3. If the repo is clean, fetch/checkout/pull `main`. If local Topography runner/input files are dirty, preserve them and fetch only.
4. Run `docs/chatgpt_status/topography/automation/topography_single_runner_bridge_20260703.ps1` through the bootstrap.
5. Run the built-in HTTP + Chrome headless smoke for 8010 and 8020.
6. Write or update:
   - `outputs/england_program_parcel_matrix_20260629/topography_updates/latest_changes.json`
   - `docs/chatgpt_status/topography/status/topography_current_status_20260703.txt`
   - `docs/chatgpt_status/topography/reports/topography_progress_latest_20260703.md`
   - `docs/chatgpt_status/topography/logs/topography_autofix_latest_20260704.log`
   - `docs/chatgpt_status/topography/heartbeat/topography_single_runner_heartbeat_latest_20260704.json`
   - `docs/chatgpt_status/topography/heartbeat/topography_bridge_heartbeat_latest_20260704.json`
   - `docs/chatgpt_status/topography/runner_state/topography_single_runner_state_20260704.json`
   - `docs/chatgpt_status/topography/browser_smoke/topography_browser_smoke_latest_20260704.json`
7. Mirror the 8020 visible output if the local AAYS output site folder exists.

## Final ready rule

`final_ready=true` is allowed only when real verified Topography parcel rows exist and include official/evidence-backed elevation above sea level, regional average, elevation difference, source URL, source date, confidence, matching method, calculation explanation, GeoJSON properties, 8020 visible latest changes, 8010 popup/panel evidence, and browser smoke.

If verified rows are missing, keep `final_ready=false` and report `verified_rows_missing`.