# Parcel Label queue contract recovery — Task 169

## Root cause

The canonical stable runner requires every queue task to include:

- `script_path` or `automation_script`
- `allowed_paths`
- valid safety flags

Tasks 161–168 were research/intent descriptors, not executable runner contracts. They were therefore skipped as invalid even while the one-click runner self-test reported queue pickup PASS.

## Recovery

Created one executable, higher-priority, single-runner task:

- Task: `169_aays1_parcel_label_backlog_visibility_orchestrator_20260711`
- Script: `docs/chatgpt_status/aays1/automation/169_parcel_label_backlog_visibility_orchestrator_20260711.ps1`
- Queue: `docs/chatgpt_status/aays1/queue/169_aays1_parcel_label_backlog_visibility_orchestrator_20260711.task.json`

The automation will process the whole existing Parcel Label research backlog in one pass. It will deduplicate candidate IDs, probe source URLs, append every unique row to the website all-rows artifact as pending, update the status/manifest/latest-change artifacts, and perform HTTP-served JSON visibility checks.

## Safety and truthfulness

- No new runner
- No parallel runner
- No geometry invented
- Unbound rows remain `NOT_BOUND`
- Source failures remain manual-review candidates
- Selenium proof is not claimed by the automation
- `final_ready=false`
- `fake_data=false`
- `db_write=false`
- `migration=false`
- `production_deploy=false`
