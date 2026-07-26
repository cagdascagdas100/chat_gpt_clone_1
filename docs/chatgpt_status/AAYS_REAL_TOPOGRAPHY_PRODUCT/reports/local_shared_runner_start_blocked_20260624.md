# Local shared runner start blocked

PAGE_KEY=AAYS_REAL_TOPOGRAPHY_PRODUCT
TASK_ID=topography_single_runner_contract_recovery_20260623T010000Z
STATUS=LOCAL_PC_ACTION_REQUIRED
REASON=The assistant can read and write GitHub files, but cannot open or control the user's local PowerShell window or start a process on the user's PC.
LOCAL_WORKTREE=C:\Users\cagda\Documents\GitHub\chat_gpt_clone_1
KNOWN_LOCAL_ERROR=git pull failed because unmerged files exist
SAFE_ACTION=Resolve or discard local merge conflict, pull, then start the existing shared runner
RUNNER_SCRIPT=docs/chatgpt_status/_shared/automation/RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER.ps1
EXPECTED_REPORT=docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/reports/topography_single_runner_contract_recovery_20260623T010000Z_v6_terminal_bridge_report.txt
PRODUCT_COMPLETION_REMAINS=93
PRODUCT_FINAL_READY=false
DO_NOT_OPEN_SECOND_RUNNER=true
DO_NOT_FAKE_FINAL_REPORT=true
