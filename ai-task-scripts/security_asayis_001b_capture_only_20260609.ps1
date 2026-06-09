$ErrorActionPreference = 'Continue'
$TaskId = 'security-asayis-001b-capture-only-20260609'
$StartedAt = Get-Date -Format s
$BridgeRoot = if ($env:AAYS_BRIDGE_ROOT) { $env:AAYS_BRIDGE_ROOT } else { 'C:\AAYS_GITHUB_BRIDGE_CLEAN2' }
$ResultDir = Join-Path $BridgeRoot 'ai-results'
$ScriptDir = Join-Path $BridgeRoot 'ai-task-scripts'
$InventoryScript = Join-Path $ScriptDir 'security_asayis_001_readonly_inventory_20260609.ps1'
New-Item -ItemType Directory -Force -Path $ResultDir | Out-Null
$CaptureMd = Join-Path $ResultDir 'security_asayis_runner_capture_latest.md'
$CaptureJson = Join-Path $ResultDir 'security_asayis_runner_capture_latest.json'
$InventoryMd = Join-Path $ResultDir 'security_asayis_latest_status.md'
$InventoryJson = Join-Path $ResultDir 'security_asayis_latest_status.json'

$lines = @()
$lines += '# SECURITY_ASAYIS_001B_CAPTURE_ONLY'
$lines += ''
$lines += 'TASK_ID=' + $TaskId
$lines += 'STATUS=STARTED'
$lines += 'STARTED_AT=' + $StartedAt
$lines += 'DB_WRITE=false'
$lines += 'DDL=false'
$lines += 'MIGRATION=false'
$lines += 'PRODUCTION_DEPLOY=false'
$lines += 'FAKE_DATA=false'
$lines += ''
$lines += '## Context'
$lines += 'BRIDGE_ROOT=' + $BridgeRoot
$lines += 'PWD=' + (Get-Location).Path
$lines += 'POWERSHELL_PID=' + $PID
$lines += 'INVENTORY_SCRIPT_EXISTS=' + (Test-Path $InventoryScript)
$lines += 'CURRENT_TASK_EXISTS=' + (Test-Path (Join-Path $BridgeRoot 'ai-tasks\current-task.json'))
$lastTask = Join-Path $BridgeRoot '.last-task-id'
$lines += 'LAST_TASK_ID_EXISTS=' + (Test-Path $lastTask)
if (Test-Path $lastTask) { $lines += 'LAST_TASK_ID=' + ((Get-Content -Raw $lastTask).Trim()) }
$lines += ''
$lines += '## Git Status Short'
try { $lines += (git -C $BridgeRoot status --short 2>&1 | Out-String).Trim() } catch { $lines += 'GIT_STATUS_ERROR=' + $_.Exception.Message }
$lines += ''
$lines += '## Inventory Invocation'
if (Test-Path $InventoryScript) {
  try {
    Push-Location $BridgeRoot
    $invOut = (& powershell -NoProfile -ExecutionPolicy Bypass -File $InventoryScript 2>&1 | Out-String)
    $invExit = $LASTEXITCODE
    Pop-Location
    $lines += 'INVENTORY_EXIT_CODE=' + $invExit
    $lines += $invOut.Trim()
  } catch {
    $lines += 'INVENTORY_INVOKE_ERROR=' + $_.Exception.Message
    try { Pop-Location } catch {}
  }
} else {
  $lines += 'INVENTORY_SCRIPT_MISSING'
}
$lines += ''
$lines += '## Result Existence'
$lines += 'INVENTORY_MD_EXISTS=' + (Test-Path $InventoryMd)
$lines += 'INVENTORY_JSON_EXISTS=' + (Test-Path $InventoryJson)
$Progress = 22
if (Test-Path $InventoryJson) {
  try {
    $json = Get-Content -Raw -Encoding UTF8 $InventoryJson | ConvertFrom-Json
    if ($json.progress_percent) { $Progress = [int]$json.progress_percent }
    $lines += 'INVENTORY_PROGRESS_PERCENT=' + $Progress
  } catch { $lines += 'INVENTORY_JSON_READ_ERROR=' + $_.Exception.Message }
}
$CompletedAt = Get-Date -Format s
$lines += 'COMPLETED_AT=' + $CompletedAt
$lines += 'PROGRESS_PERCENT=' + $Progress
$lines += 'NEXT_COMMAND=devam et'
Set-Content -Encoding UTF8 -Path $CaptureMd -Value $lines
$obj = [ordered]@{
  task_id=$TaskId; status='FINISHED_CAPTURE_ONLY'; progress_percent=$Progress; started_at=$StartedAt; completed_at=$CompletedAt;
  db_write=$false; ddl=$false; migration=$false; production_deploy=$false; fake_data=$false;
  inventory_script_exists=(Test-Path $InventoryScript); inventory_md_exists=(Test-Path $InventoryMd); inventory_json_exists=(Test-Path $InventoryJson); next_command='devam et'
}
$obj | ConvertTo-Json -Depth 6 | Set-Content -Encoding UTF8 -Path $CaptureJson
$lines -join "`n"
exit 0
