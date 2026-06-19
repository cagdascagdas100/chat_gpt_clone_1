$ErrorActionPreference = 'Continue'
$pageKey = 'security_public_safety_low_credit_20260612'
$taskId = 'security_public_safety_20260619_df_parcel_contract'
$base = Split-Path -Parent $PSScriptRoot
$reports = Join-Path $base 'reports'
$statusDir = Join-Path $base 'status'
$outDir = Join-Path $base 'runner_outputs'
$heartDir = Join-Path $base 'heartbeat'
New-Item -ItemType Directory -Force -Path $reports,$statusDir,$outDir,$heartDir | Out-Null
$ts = Get-Date -Format 'yyyyMMdd_HHmmss'
$runnerOutput = Join-Path $outDir "security_20260619_df_headerfix_runner_output_$ts.md"
$source = Join-Path $PSScriptRoot 'security_public_safety_20260619_df_parcel_contract_task.ps1'
$temp = Join-Path $env:TEMP "security_public_safety_20260619_df_parcel_contract_task_fixed_$ts.ps1"
@('status=HEADERFIX_WRAPPER_STARTED',"page_key=$pageKey","task_id=$taskId","source=$source","temp=$temp",'separate_runner=false','powershell_required_from_user=false') | Out-File -FilePath $runnerOutput -Encoding utf8
if (-not (Test-Path $source)) {
  @('status=BLOCKED','reason=source_script_missing') | Out-File -FilePath $runnerOutput -Append -Encoding utf8
  exit 0
}
$raw = Get-Content -Path $source -Raw
$fixed = $raw
if ($raw -match '^\$ErrorActionPreference\s*=\s*[''\"].*?[''\"]\s*\r?\n\s*param\(') {
  $fixed = $raw -replace '^\$ErrorActionPreference\s*=\s*[''\"].*?[''\"]\s*\r?\n',''
  $marker = "`n`$RequiredFields"
  if ($fixed.Contains($marker)) {
    $fixed = $fixed.Replace($marker, "`n`$ErrorActionPreference = 'Continue'`n`n`$RequiredFields")
  } else {
    $fixed = "$fixed`n`n`$ErrorActionPreference = 'Continue'`n"
  }
}
Set-Content -Path $temp -Value $fixed -Encoding utf8
& $temp
$code = $LASTEXITCODE
@('status=HEADERFIX_WRAPPER_COMPLETED',"exit_code=$code","completed_at=$((Get-Date).ToString('s'))") | Out-File -FilePath $runnerOutput -Append -Encoding utf8
exit 0
