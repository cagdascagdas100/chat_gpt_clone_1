$ErrorActionPreference = 'Stop'
$Page = 'AAYS_REAL_TOPOGRAPHY_PRODUCT'
$Branch = 'aays-runner-v17-icon-work-20260603-232706'
$Now = Get-Date -Format 'yyyyMMdd-HHmmss'
$UtcNow = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
$RepoRoot = Get-Location
$StatusRoot = Join-Path $RepoRoot "docs/chatgpt_status/$Page"
$Reports = Join-Path $StatusRoot 'reports'
$Status = Join-Path $StatusRoot 'status'
$Heartbeat = Join-Path $StatusRoot 'heartbeat'
$CurrentTaskDir = Join-Path $StatusRoot 'current-task'
$Control = Join-Path $StatusRoot 'control'
$Queue = Join-Path $StatusRoot 'queue'
$RunnerTasks = Join-Path $StatusRoot 'runner_tasks'
$Automation = Join-Path $StatusRoot 'automation'
New-Item -ItemType Directory -Force -Path $Reports,$Status,$Heartbeat,$CurrentTaskDir,$Control,$Queue,$RunnerTasks,$Automation | Out-Null

function Safe-GetChildItems {
  param([string]$Path, [string]$Filter='*', [int]$Take=20)
  if (-not (Test-Path $Path)) { return @() }
  return @(Get-ChildItem -Path $Path -Filter $Filter -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First $Take)
}

function Line([string]$Text) { Add-Content -Path $script:Report -Value $Text -Encoding UTF8 }

$script:Report = Join-Path $Reports "terrayield_047_output_harvest_stuck_recovery_$Now.txt"
$ProgressFile = Join-Path $Status "chatgpt_progress_047_harvest_status_probe_$Now.txt"
$HeartbeatFile = Join-Path $Heartbeat "heartbeat_047_harvest_status_probe_$Now.txt"

$GitBranch = 'unknown'
try { $GitBranch = (git rev-parse --abbrev-ref HEAD 2>$null).Trim() } catch { $GitBranch = 'git_unavailable' }
$GitStatus = 'unknown'
try { $GitStatus = (git status --short 2>$null | Select-Object -First 50) -join '; ' } catch { $GitStatus = 'git_status_unavailable' }
if ([string]::IsNullOrWhiteSpace($GitStatus)) { $GitStatus = 'clean_or_no_short_output' }

$ExpectedNames = @(
  'terrayield_047_output_harvest_stuck_recovery_*.txt',
  'runner_poller_local_diagnosis_*.txt',
  'runner_contract_inventory_*.txt',
  '*046*',
  '*044*',
  'topography_real_lookup_endpoint_smoke_*.txt',
  'runner_target_branch_contract_probe_*.txt'
)

$BridgeRoot = 'C:\AAYS_GITHUB_BRIDGE_CLEAN2'
$BridgeResults = Join-Path $BridgeRoot 'ai-results'
$BridgeHeartbeat = Join-Path $BridgeRoot 'ai-heartbeat'
$BridgeLogs = Join-Path $BridgeRoot 'ai-runner-logs'
$LocalAays = 'C:\Users\cagda\Documents\GitHub\AAYS'
$LocalTi = Join-Path $LocalAays 'terrayield_land_intelligence'
$BackendHealthNotes = @()
foreach ($url in @('http://127.0.0.1:8010/health','http://localhost:8010/health')) {
  try {
    $resp = Invoke-WebRequest -UseBasicParsing -Uri $url -TimeoutSec 5
    $BackendHealthNotes += "$url => HTTP $($resp.StatusCode)"
  } catch {
    $BackendHealthNotes += "$url => unavailable: $($_.Exception.Message)"
  }
}

$CurrentTaskPath = Join-Path $RepoRoot 'ai-tasks/current-task.json'
$CurrentTaskText = ''
if (Test-Path $CurrentTaskPath) { $CurrentTaskText = Get-Content $CurrentTaskPath -Raw -ErrorAction SilentlyContinue }

Set-Content -Path $Report -Encoding UTF8 -Value "TerraYield / AAYS REAL TOPOGRAPHY PRODUCT - 047 harvest/stuck recovery probe"
Line "TIME_UTC=$UtcNow"
Line "PAGE_KEY=$Page"
Line "BRANCH_EXPECTED=$Branch"
Line "BRANCH_ACTUAL=$GitBranch"
Line "MODE=READ_ONLY_HARVEST_AND_STUCK_RECOVERY_PROBE"
Line "DB_WRITE=False"
Line "MIGRATION=False"
Line "PRODUCTION_DEPLOY=False"
Line "FAKE_DATA=False"
Line ""
Line "== CURRENT TASK =="
Line $CurrentTaskText
Line ""
Line "== GIT STATUS SHORT =="
Line $GitStatus
Line ""
Line "== TARGET STATUS ROOT =="
Line "StatusRoot=$StatusRoot"
foreach ($dir in @($Reports,$Status,$Heartbeat,$CurrentTaskDir,$Control,$Queue,$RunnerTasks,$Automation)) {
  Line "DIR_CHECK=$dir EXISTS=$(Test-Path $dir)"
}
Line ""
Line "== REPORT INVENTORY =="
foreach ($pattern in $ExpectedNames) {
  $items = Safe-GetChildItems -Path $Reports -Filter $pattern -Take 10
  Line "PATTERN=$pattern COUNT=$($items.Count)"
  foreach ($item in $items) { Line "  $($item.LastWriteTime.ToString('s')) size=$($item.Length) name=$($item.Name)" }
}
Line ""
Line "== STATUS INVENTORY =="
foreach ($item in (Safe-GetChildItems -Path $Status -Filter '*.txt' -Take 20)) { Line "STATUS_FILE $($item.LastWriteTime.ToString('s')) size=$($item.Length) name=$($item.Name)" }
Line ""
Line "== HEARTBEAT INVENTORY =="
foreach ($item in (Safe-GetChildItems -Path $Heartbeat -Filter '*.txt' -Take 20)) { Line "HEARTBEAT_FILE $($item.LastWriteTime.ToString('s')) size=$($item.Length) name=$($item.Name)" }
Line ""
Line "== BRIDGE LOCAL CHECKS =="
Line "BridgeRootExists=$(Test-Path $BridgeRoot)"
Line "BridgeResultsExists=$(Test-Path $BridgeResults)"
Line "BridgeHeartbeatExists=$(Test-Path $BridgeHeartbeat)"
Line "BridgeLogsExists=$(Test-Path $BridgeLogs)"
foreach ($item in (Safe-GetChildItems -Path $BridgeResults -Filter '*realtopography*' -Take 20)) { Line "BRIDGE_RESULT_REALT $($item.LastWriteTime.ToString('s')) size=$($item.Length) name=$($item.Name)" }
foreach ($item in (Safe-GetChildItems -Path $BridgeResults -Filter '*topography*' -Take 20)) { Line "BRIDGE_RESULT_TOPO $($item.LastWriteTime.ToString('s')) size=$($item.Length) name=$($item.Name)" }
foreach ($item in (Safe-GetChildItems -Path $BridgeResults -Filter '*046*' -Take 20)) { Line "BRIDGE_RESULT_046 $($item.LastWriteTime.ToString('s')) size=$($item.Length) name=$($item.Name)" }
foreach ($item in (Safe-GetChildItems -Path $BridgeResults -Filter '*044*' -Take 20)) { Line "BRIDGE_RESULT_044 $($item.LastWriteTime.ToString('s')) size=$($item.Length) name=$($item.Name)" }
foreach ($item in (Safe-GetChildItems -Path $BridgeLogs -Filter '*.log' -Take 10)) { Line "BRIDGE_LOG $($item.LastWriteTime.ToString('s')) size=$($item.Length) name=$($item.Name)" }
Line ""
Line "== LOCAL AAYS CHECKS =="
Line "LocalAaysExists=$(Test-Path $LocalAays)"
Line "LocalTerraYieldExists=$(Test-Path $LocalTi)"
Line ""
Line "== BACKEND HEALTH PROBE =="
foreach ($note in $BackendHealthNotes) { Line $note }
Line ""
Line "== DECISION =="
$FinalSmoke = Safe-GetChildItems -Path $Reports -Filter 'topography_real_lookup_endpoint_smoke_*.txt' -Take 1
if ($FinalSmoke.Count -gt 0) {
  Line "FINAL_SMOKE_FOUND=True"
  Line "FINAL_SMOKE_LATEST=$($FinalSmoke[0].Name)"
  Line "FINAL_READY=ReviewRequired"
} else {
  Line "FINAL_SMOKE_FOUND=False"
  Line "FINAL_READY=False"
  Line "NEXT_REQUIRED=produce_or_run_topography_real_lookup_endpoint_smoke report after endpoint/data verification"
}
Line ""
Line "SUMMARY=047 harvest probe completed. Review this file plus latest status/heartbeat files before queuing heavier data work."

Set-Content -Path $ProgressFile -Encoding UTF8 -Value "PAGE_KEY=$Page`nSTATUS=047_HARVEST_STATUS_PROBE_WRITTEN`nTIME_UTC=$UtcNow`nLATEST_REPORT=docs/chatgpt_status/$Page/reports/terrayield_047_output_harvest_stuck_recovery_$Now.txt`nFINAL_READY=False`nDB_WRITE=False`nMIGRATION=False`nPRODUCTION_DEPLOY=False`nFAKE_DATA=False`n"
Set-Content -Path $HeartbeatFile -Encoding UTF8 -Value "PAGE_KEY=$Page`nHEARTBEAT_AT=$Now`nSTATUS=047_HARVEST_STATUS_PROBE_WRITTEN`nSCRIPT=aays_realtopography_047_harvest_status_probe.ps1`n"
Write-Host "WROTE_REPORT=$Report"
Write-Host "WROTE_STATUS=$ProgressFile"
Write-Host "WROTE_HEARTBEAT=$HeartbeatFile"
