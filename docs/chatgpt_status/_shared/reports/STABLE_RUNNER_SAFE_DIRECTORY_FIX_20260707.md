# Stable Runner Safe Directory Fix - 2026-07-07

Status: fixed in branch codex/aays-single-runner-v5-20260706

Root cause:
- Stable runner was selected correctly, but git status/fetch/rebase calls could fail under a different Windows/Codex user with Git dubious ownership / safe.directory protection.
- Global git config was not reliable because C:\Users\cagda\.gitconfig could be locked or permission denied from the runner context.

Change:
- RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_STABLE_20260707.ps1 now injects exact local safe.directory values into every runner git call.
- This avoids requiring global git config and keeps the single shared runner contract intact.

Verification:
- PowerShell parser check passed.
- One-shot stable runner scan with -NoPush -ScanOnly returned exit_code=0.
- Previous RUNNER_FATAL: STATUS_FAILED blocker no longer appears in the latest test output.

Known remaining state:
- final_ready=false
- product_final_ready=false
- fake_data=false
- db_write=false
- migration=false
- production_deploy=false
- Runtime status/log files remain local runtime outputs and are intentionally not committed by this fix.
