param(
  [string]$WorktreeRoot = "F:\chatgpt\AAYS_WORK\security_public_safety_20260622_clean"
)

$ErrorActionPreference = "Stop"
$pageKey = "security_public_safety_low_credit_20260612"
$reportRoot = Join-Path $WorktreeRoot "docs\chatgpt_status\$pageKey\reports"
New-Item -ItemType Directory -Force -Path $reportRoot | Out-Null
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$reportPath = Join-Path $reportRoot "security_chatgpt_runner_instruction_$stamp.md"
$lines = @()
$lines += "# Security ChatGPT Runner Instruction"
$lines += "generated_at: $(Get-Date -Format s)"
$lines += "worktree_root: $WorktreeRoot"
$lines += "status: QUEUED_FOR_LOCAL_PATCH_PACKAGE"
$lines += "next_action: Apply the ChatGPT local patch bundle security_chatgpt_gap_apply_bundle_20260622.zip, then run the smoke script from the uploaded package."
$lines += "final_decision: BLOCKED_MISSING_REAL_PARCEL_CARRIER_OR_CANONICAL_FIELDS until polygon render and canonical popup/right-panel proof pass."
Set-Content -Path $reportPath -Value $lines -Encoding UTF8
Write-Output $reportPath
