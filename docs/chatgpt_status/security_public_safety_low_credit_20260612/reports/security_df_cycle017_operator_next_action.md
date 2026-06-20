# Security DF cycle017 next action

page_key: security_public_safety_low_credit_20260612
task_id: security_public_safety_20260619_df_parcel_contract
status: RUNNER_OUTPUT_PENDING
completion_percent: 97

Current known chain:
- queue cycle: 015
- current-task cycle: 015
- latest status cycle: 016
- run script: docs/chatgpt_status/security_public_safety_low_credit_20260612/automation/vrun.ps1
- target wrapper: docs/chatgpt_status/security_public_safety_low_credit_20260612/automation/security_public_safety_20260619_df_headerfix_wrapper.ps1

Missing evidence:
- runner output report
- smoke report
- final wrapper with accepted completion markers

Next required action:
- single shared runner must pick the page queue and run vrun.ps1
- after runner publishes files, inspect reports/security_df_worktree_final_wrapper_YYYYMMDD_HHMMSS.md
- do not mark completion as 100 until the runner generated final wrapper confirms completion

PowerShell required from user: false
Separate runner required: false
