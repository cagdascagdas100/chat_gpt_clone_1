PAGE_KEY=gas_emissions
DATE=2026-06-24
STATUS=BLOCKED_MAIN_BRANCH_PROOF

total_percent=89
why_percent_changed_or_not=local feature-branch files claim FINAL_READY=100, but runner pickup and push to GitHub main are not proven from this checkout; preserved at 89
runner_pickup=not_proven
runner_push=not_proven
expected_next_report=docs/chatgpt_status/gas_emissions/reports/gas_emissions_finalizer_result_20260622_2300.md
blockers=local repo branch is feature/terrayield-aays-integration not main; finalizer file exists only in this local checkout state; generic runner_outputs path is also being used outside page-key root; no verified main-branch push proof
powershell_required_from_user=false
if_required_exact_single_command=none
wait_minutes=0
final_ready=false

DETAILS
- Existing local status file:
  docs/chatgpt_status/gas_emissions/status/terrayield-088-gas-emissions-proxy-finalize.txt
  says completion_percent=100 and final_ready=true
- This is not accepted as main-branch proof under the current task rules because:
  1. current local branch is not main
  2. runner pickup is not proven
  3. push to GitHub main is not proven
