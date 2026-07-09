# AAYS1 137 - 114 runner pickup schema fix

## Root cause

114 was not being picked up because the queue file was not compatible with the runner pickup pattern used by working tasks.

Working example: `104_visible_expansion_orchestrator_20260709.task.json` uses:

- `status: pending`
- `script: docs/chatgpt_status/aays1/automation/104_visible_expansion_orchestrator.ps1`
- `expected_outputs`

The previous 114 queue used force-pickup status text but did not provide a runner-executable `script` field, so the healthy runner had no script to run for 114.

## Fix applied

- Added automation script:
  `docs/chatgpt_status/aays1/automation/114_live_source_verification_from_113_candidates.ps1`

- Updated queue:
  `docs/chatgpt_status/aays1/queue/114_aays1_live_source_verification_from_113_candidates_20260709.task.json`

- New queue fields:
  - `status: pending`
  - `script: docs/chatgpt_status/aays1/automation/114_live_source_verification_from_113_candidates.ps1`
  - `expected_outputs` for status/report/runner output

## Safety

- New runner: false
- Parallel runner: false
- Existing F portable single runner only
- final_ready=false
- fake_data=false
- db_write=false
- migration=false
- production_deploy=false

## Current expected next output

`docs/chatgpt_status/aays1/status/114_aays1_live_source_verification_latest.json`

No product metric was increased yet. The next increase requires real 114 output and downstream CSV/GeoJSON/product integration evidence.
