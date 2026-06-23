# CURRENT TASK - AAYS_REAL_TOPOGRAPHY_PRODUCT

TASK_ID=topography_single_runner_contract_recovery_20260623T010000Z
PAGE_KEY=AAYS_REAL_TOPOGRAPHY_PRODUCT
CURRENT_TASK_STATUS=READY_FOR_SINGLE_RUNNER
AUTOMATION=docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/automation/topography_single_runner_contract_recovery_20260623T010000Z.ps1

## Do next

The existing single shared runner should pick up and execute the automation path above. If the runner contract differs, the automation must first detect the contract and write the detected layout to:

`docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/reports/topography_single_runner_contract_recovery_20260623T010000Z_runner_contract_detect.txt`

## Do not do

- Do not start a second runner.
- Do not create a different page-key.
- Do not write outside `docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/` except read-only diagnostics of existing source/data paths.
- Do not claim product 100 unless real final evidence exists.
