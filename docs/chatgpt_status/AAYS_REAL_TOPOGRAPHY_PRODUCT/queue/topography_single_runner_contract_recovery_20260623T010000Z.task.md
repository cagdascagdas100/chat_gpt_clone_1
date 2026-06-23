# QUEUED TASK - AAYS_REAL_TOPOGRAPHY_PRODUCT

TASK_ID=topography_single_runner_contract_recovery_20260623T010000Z
PAGE_KEY=AAYS_REAL_TOPOGRAPHY_PRODUCT
TASK_STATUS=QUEUED
TASK_KIND=single_runner_contract_recovery_then_parallel_readonly_audit
AUTOMATION=docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/automation/topography_single_runner_contract_recovery_20260623T010000Z.ps1
EXPECTED_STATUS=docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/status/topography_single_runner_contract_recovery_20260623T010000Z_final.status.txt
EXPECTED_REPORT=docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/reports/topography_single_runner_contract_recovery_20260623T010000Z_final_report.txt

## Goal

Continue the Topography handoff without fake completion and without creating a second runner. The single shared runner must execute the automation script above and produce GitHub-visible reports under this page-key.

## Required phases

1. Detect actual runner/queue/current-task contract from the local worktree.
2. Verify local technical final tokens already claimed by handoff:
   - FINAL_STATUS=FINAL_READY_CONFIRMED
   - PRODUCT_PROGRESS_ESTIMATE=100
   - PRODUCTION_COMPLETE=true
3. Run independent read-only audits in non-conflicting output files:
   - remote branch sync / divergence diagnostic
   - England-wide and London-only topography data coverage audit
   - parcel lookup coverage audit for `no_data` rate
   - static UI contract audit for popup/right panel functions and hight_differance.png reference
   - naming debt audit for `pb_*` under this page-key
4. Aggregate all outputs into final report and final status.

## Completion rule

Only write `FINAL_STATUS=FINAL_READY_CONFIRMED`, `PRODUCT_PROGRESS_ESTIMATE=100`, and `PRODUCTION_COMPLETE=true` in the final status if all required evidence is present in the generated reports. Otherwise write `FINAL_STATUS=BLOCKED_NEEDS_EVIDENCE` with exact blockers.

## Safety

No DB writes, no migrations, no production deploys, no seed/fake data, no force-push, no second runner.
