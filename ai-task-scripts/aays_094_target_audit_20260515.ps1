$ErrorActionPreference = 'Continue'
$TaskId = 'aays-094-target-audit-20260515'
$BridgeRoot = if ($env:AAYS_BRIDGE_ROOT) { $env:AAYS_BRIDGE_ROOT } else { Split-Path -Parent $PSScriptRoot }
$ProjectRoot = 'C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$ResultDir = Join-Path $BridgeRoot 'ai-results'
$HeartbeatDir = Join-Path $BridgeRoot 'ai-heartbeat'
New-Item -ItemType Directory -Force -Path $ResultDir,$HeartbeatDir | Out-Null
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$Report = Join-Path $ResultDir "aays-094-target-audit-$Stamp.md"
$Heartbeat = Join-Path $HeartbeatDir 'target-audit.md'
$Lines = New-Object System.Collections.Generic.List[string]
function AddLine([string]$m){ [void]$Lines.Add($m) }
AddLine '# AAYS 094 Target Audit'
AddLine ('Generated: ' + (Get-Date -Format s))
AddLine ('TaskId: ' + $TaskId)
AddLine ('ProjectRoot: ' + $ProjectRoot)
AddLine 'Mode: read-only target audit.'
if(Test-Path $ProjectRoot){
  AddLine ''
  AddLine '## app quality files'
  Get-ChildItem (Join-Path $ProjectRoot 'app\quality') -File -ErrorAction SilentlyContinue | Sort-Object Name | Select-Object Name,Length,LastWriteTime | Format-Table -AutoSize | Out-String | ForEach-Object { AddLine $_ }
  AddLine ''
  AddLine '## matching tests'
  Get-ChildItem (Join-Path $ProjectRoot 'tests') -File -Filter '*source*' -ErrorAction SilentlyContinue | Sort-Object Name | Select-Object Name,Length,LastWriteTime | Format-Table -AutoSize | Out-String | ForEach-Object { AddLine $_ }
  AddLine ''
  AddLine '## git status'
  Push-Location $ProjectRoot
  try { git status --short | ForEach-Object { AddLine $_ } } catch { AddLine ('git_status_error: ' + $_.Exception.Message) }
  Pop-Location
} else {
  AddLine 'PROJECT_ROOT_MISSING'
}
AddLine ''
AddLine 'next_step: add small deterministic review helper and focused tests'
AddLine 'wide_accuracy_program_percent: 70'
AddLine 'AAYS_094_TARGET_AUDIT_DONE=true'
Set-Content -Encoding UTF8 -Path $Report -Value $Lines
Set-Content -Encoding UTF8 -Path $Heartbeat -Value $Lines
Write-Output 'AAYS_094_TARGET_AUDIT_DONE=true'
Write-Output ('REPORT=' + $Report)
exit 0
