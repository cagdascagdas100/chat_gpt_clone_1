$ErrorActionPreference = "Continue"
$script = Join-Path $PSScriptRoot "security_public_safety_20260619_df_parcel_contract_task.ps1"
$base = Split-Path -Parent $PSScriptRoot
$reports = Join-Path $base "reports"
$statusDir = Join-Path $base "status"
$heartbeatDir = Join-Path $base "heartbeat"
New-Item -ItemType Directory -Force -Path $reports,$statusDir,$heartbeatDir | Out-Null
$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$shimReport = Join-Path $reports "security_20260619_df_vrun_shim_$ts.md"
@(
  "status: VRUN_SHIM_STARTED",
  "page_key: security_public_safety_low_credit_20260612",
  "task_id: security_public_safety_20260619_df_parcel_contract",
  "script: $script",
  "separate_runner_spawned: false",
  "powershell_required_from_user: false",
  "git_add_dot: false",
  "started_at: $((Get-Date).ToString('s'))"
) | Out-File -FilePath $shimReport -Encoding utf8
if (Test-Path $script) {
  & $script
  $code = $LASTEXITCODE
  @("status: VRUN_SHIM_COMPLETED", "exit_code: $code", "completed_at: $((Get-Date).ToString('s'))") | Out-File -FilePath $shimReport -Append -Encoding utf8
  exit 0
}
@("status: VRUN_SHIM_BLOCKED", "reason: target_script_missing", "script: $script") | Out-File -FilePath $shimReport -Append -Encoding utf8
exit 0
