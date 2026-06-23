# Gas Emissions Runner Pickup Contract Gap

PAGE_KEY=gas_emissions
TASK_ID=gas-emissions-single-runner-finalizer-20260622_2300
STATUS=RUNNER_PICKUP_CONTRACT_NOT_PROVEN_FROM_GITHUB
COMPLETION_PERCENT=89
CAN_MARK_100_PERCENT=false

## What was checked

The following GitHub repository searches were run against `cagdascagdas100/chat_gpt_clone_1` on branch `feature/terrayield-aays-integration` context:

- `RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER`
- `current-task`
- `single_runner queue`
- `gas_emissions_finalizer_20260622_2300`

No repository search result confirmed the real shared-runner pickup contract.

## Existing valid task files

The gas emissions page-key already contains the task contract files:

- `docs/chatgpt_status/gas_emissions/queue/gas_emissions_finalizer_20260622_2300.queue.json`
- `docs/chatgpt_status/gas_emissions/automation/gas_emissions_single_runner_finalizer_20260622_2300.ps1`
- `docs/chatgpt_status/gas_emissions/status/gas_emissions_finalizer_status_20260622_2300.json`
- `docs/chatgpt_status/gas_emissions/heartbeat/gas_emissions_finalizer_heartbeat_20260622_2300.json`
- `docs/chatgpt_status/gas_emissions/reports/gas_emissions_finalizer_result_20260622_2300.md`

## Blocker

The heartbeat still says `queued_with_real_automation_script_written`, so the enhanced script has not been executed by the single shared runner.

## Why no percent increase

The product patch and enhanced runtime probe script already exist. The missing item is not another product file. The missing item is runner execution proof written back to GitHub.

## Safe next condition

Do not mark `FINAL_READY` until the GitHub status/report contains:

- runner execution started/finished evidence
- node syntax PASS
- dataset feature count > 0
- HTTP 200 checks for health, app, geojson, and air icon
- runtime `geometryMode=polygon_join`
- non-empty gas popup or side-panel field proof
