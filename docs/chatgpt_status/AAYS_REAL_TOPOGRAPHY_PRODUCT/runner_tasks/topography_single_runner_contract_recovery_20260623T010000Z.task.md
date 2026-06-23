# RUNNER TASK - AAYS_REAL_TOPOGRAPHY_PRODUCT

TASK_ID=topography_single_runner_contract_recovery_20260623T010000Z
PAGE_KEY=AAYS_REAL_TOPOGRAPHY_PRODUCT
RUNNER_CONTRACT_STATUS=UNKNOWN_AT_CHATGPT_TIME
AUTOMATION=docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/automation/topography_single_runner_contract_recovery_20260623T010000Z.ps1

## Single runner instruction

Execute only the automation file above. Do not spawn another queue runner, watcher, bridge, or polling process.

The automation may run non-conflicting read-only audit branches internally and must write each branch result to a separate report path. It must not make DB, migration, deploy, seed, or production writes.

## Expected report artifacts

- `reports/topography_single_runner_contract_recovery_20260623T010000Z_runner_contract_detect.txt`
- `reports/topography_single_runner_contract_recovery_20260623T010000Z_final_token_verify.txt`
- `reports/topography_single_runner_contract_recovery_20260623T010000Z_remote_sync_diagnostic.txt`
- `reports/topography_single_runner_contract_recovery_20260623T010000Z_data_coverage_audit.txt`
- `reports/topography_single_runner_contract_recovery_20260623T010000Z_lookup_coverage_audit.txt`
- `reports/topography_single_runner_contract_recovery_20260623T010000Z_ui_static_contract_audit.txt`
- `reports/topography_single_runner_contract_recovery_20260623T010000Z_naming_debt_audit.txt`
- `reports/topography_single_runner_contract_recovery_20260623T010000Z_final_report.txt`
- `status/topography_single_runner_contract_recovery_20260623T010000Z_final.status.txt`

## Finish decision

If every blocker is closed by real evidence, mark final ready. If not, keep product completeness below 100 and list the exact remaining blocker names.
