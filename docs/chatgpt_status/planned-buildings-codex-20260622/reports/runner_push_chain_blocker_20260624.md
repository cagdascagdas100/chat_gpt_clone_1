PAGE_KEY=planned-buildings-codex-20260622
DATE=2026-06-24
STATUS=BLOCKED_RUNNER_CONTRACT_AND_PUSH_CHAIN

total_percent=81
why_percent_changed_or_not=planned-buildings current local evidence does not prove runner pickup, DB/API/browser smoke, or main-branch push; preserved at 81
runner_pickup=not_proven
runner_push=not_proven
expected_next_report=docs/chatgpt_status/planned-buildings-codex-20260622/reports/planned_buildings_runner_orchestrator_latest.txt
blockers=local repo is not on main; active shared runner contract currently points at security current-task; no proven execution of planned_buildings_final_ready_orchestrator_latest.ps1; no proven HTTP 200 + browser evidence + popup/right-panel evidence on main
powershell_required_from_user=false
if_required_exact_single_command=none
wait_minutes=0
final_ready=false

DETAILS
- Existing detector file is present:
  docs/chatgpt_status/planned-buildings-codex-20260622/reports/planned_buildings_contract_detector_latest.txt
- Existing detector reports only minimal queue compatibility and progress 76.
- Required final orchestrator report is not proven from main-branch runner execution.
- Active bridge task currently points to security_public_safety_low_credit_20260612, not planned-buildings.
- No honest FINAL_READY can be written without live map, non-empty features, parcel popup evidence, and API 200 proofs on the correct branch.
