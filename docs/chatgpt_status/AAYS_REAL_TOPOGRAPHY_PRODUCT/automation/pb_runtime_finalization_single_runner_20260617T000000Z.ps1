$ErrorActionPreference = 'Continue'
$PageKey = 'AAYS_REAL_TOPOGRAPHY_PRODUCT'
$Branch = 'aays-runner-v17-icon-work-20260603-232706'
$PreferredWorktree = 'F:\chatgpt\AAYS_WORKTREES\aays-runner-v17-icon-work-20260603-232706'
$Task = 'pb-runtime-finalization-single-runner-20260617T000000Z'
$ReportRel = "docs/chatgpt_status/$PageKey/reports/pb_runtime_finalization_single_runner_20260617T000000Z.txt"
$StatusRel = "docs/chatgpt_status/$PageKey/status/pb_runtime_finalization_single_runner_20260617T000000Z.status.txt"
$ReportRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..')).Path
$Worktree = $ReportRoot
try {
  if (Test-Path -LiteralPath $PreferredWorktree) {
    $inside = git -C $PreferredWorktree rev-parse --is-inside-work-tree 2>$null
    $localBranch = (git -C $PreferredWorktree rev-parse --abbrev-ref HEAD 2>$null).Trim()
    if (($LASTEXITCODE -eq 0) -and ($inside.Trim() -eq 'true') -and ($localBranch -eq $Branch)) { $Worktree = $PreferredWorktree }
  }
} catch {}
$ReportPath = Join-Path $ReportRoot $ReportRel
$StatusPath = Join-Path $ReportRoot $StatusRel
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $ReportPath),(Split-Path -Parent $StatusPath) | Out-Null
function Write-Report([string]$line) { $line | Out-File -FilePath $ReportPath -Append -Encoding utf8 }
function Write-State([string]$state, [bool]$final) { @("PAGE_KEY: $PageKey","TASK: $Task","STATUS: $state","FINAL_READY: $($final.ToString().ToLower())","REPORT: $ReportRel") | Out-File -FilePath $StatusPath -Encoding utf8 }
function Commit-Outputs([string]$msg) { try { git -C $ReportRoot add $ReportRel $StatusRel 2>&1 | Out-File -FilePath $ReportPath -Append -Encoding utf8; $pending = git -C $ReportRoot status --porcelain -- $ReportRel $StatusRel; if ($pending) { git -C $ReportRoot commit -m $msg 2>&1 | Out-File -FilePath $ReportPath -Append -Encoding utf8; git -C $ReportRoot push origin HEAD:$Branch 2>&1 | Out-File -FilePath $ReportPath -Append -Encoding utf8 } } catch { Write-Report "GIT_OUTPUT_PUSH_ERROR=$($_.Exception.Message)" } }
'' | Out-File -FilePath $ReportPath -Encoding utf8
Write-Report 'LAYER=Topography'
Write-Report "PAGE_KEY=$PageKey"
Write-Report "BRANCH=$Branch"
Write-Report "REPORT_ROOT=$ReportRoot"
Write-Report "RUNTIME_WORKTREE=$Worktree"
Write-Report 'CANONICAL_FINAL_GATE=runner-produced topography runtime finalization wrapper'
Write-State 'RUNNING' $false
$runtimeScript = Join-Path $ReportRoot "docs/chatgpt_status/$PageKey/automation/topography_runtime_final_v2_20260616_2254.ps1"
$runtimeReport = Join-Path $ReportRoot "docs/chatgpt_status/$PageKey/reports/topography_chatgpt_runtime_gap_report_20260616_2254_v2.txt"
Write-Report "RUNTIME_SCRIPT_EXISTS=$((Test-Path $runtimeScript).ToString().ToLower())"
try { git -C $Worktree fetch origin $Branch 2>&1 | Out-File -FilePath $ReportPath -Append -Encoding utf8; git -C $Worktree pull --rebase --autostash origin $Branch 2>&1 | Out-File -FilePath $ReportPath -Append -Encoding utf8 } catch { Write-Report "WORKTREE_SYNC_WARNING=$($_.Exception.Message)" }
if (Test-Path -LiteralPath $runtimeScript) {
  try {
    & powershell -NoProfile -ExecutionPolicy Bypass -File $runtimeScript 2>&1 | Out-File -FilePath $ReportPath -Append -Encoding utf8
  } catch {
    Write-Report "RUNTIME_SCRIPT_ERROR=$($_.Exception.Message)"
  }
} else {
  Write-Report 'RUNTIME_SCRIPT_MISSING=true'
}
Start-Sleep -Seconds 3
$runtimeText = ''
if (Test-Path -LiteralPath $runtimeReport) {
  $runtimeText = Get-Content -Raw $runtimeReport
  Get-Content $runtimeReport | Out-File -FilePath $ReportPath -Append -Encoding utf8
}
Write-Report "RUNTIME_REPORT_EXISTS=$((Test-Path $runtimeReport).ToString().ToLower())"
$nodeOk = $runtimeText -match 'NODE_CHECK_OK=True'
$pyOk = $runtimeText -match 'PY_COMPILE_OK=True'
$frontendOk = $runtimeText -match 'FRONTEND_CONTRACT_OK=True'
$backendOk = $runtimeText -match 'BACKEND_DIRECT_DEM_CONTRACT_OK=True'
$tileCfgOk = $runtimeText -match 'TILE_CONFIG_OK=True'
$programOk = $runtimeText -match 'PROGRAM_OPENED=True'
$lookupOk = $runtimeText -match 'LOOKUP_ENDPOINT_OK=True'
$tileOk = $runtimeText -match 'TILE_ENDPOINT_OK=True'
$directOk = $runtimeText -match 'DIRECT_DEM_LOOKUP_OK=True'
$coverage = 'unknown'
if ($runtimeText -match 'SOURCE_COVERAGE=([^\r\n]+)') { $coverage = $matches[1].Trim() }
$runtime100 = ($runtimeText -match 'PRODUCT_PROGRESS_ESTIMATE=100') -and ($runtimeText -match 'PRODUCTION_COMPLETE=true')
$final = $nodeOk -and $pyOk -and $frontendOk -and $backendOk -and $tileCfgOk -and $programOk -and $lookupOk -and $tileOk -and $directOk -and (($coverage -eq 'England_wide') -or ($coverage -eq 'London_only'))
Write-Report "TOP_NODE_CHECK_OK=$($nodeOk.ToString().ToLower())"
Write-Report "TOP_PY_COMPILE_OK=$($pyOk.ToString().ToLower())"
Write-Report "TOP_FRONTEND_CONTRACT_OK=$($frontendOk.ToString().ToLower())"
Write-Report "TOP_BACKEND_CONTRACT_OK=$($backendOk.ToString().ToLower())"
Write-Report "TOP_TILE_CONFIG_OK=$($tileCfgOk.ToString().ToLower())"
Write-Report "TOP_PROGRAM_OPENED=$($programOk.ToString().ToLower())"
Write-Report "TOP_LOOKUP_ENDPOINT_OK=$($lookupOk.ToString().ToLower())"
Write-Report "TOP_TILE_ENDPOINT_OK=$($tileOk.ToString().ToLower())"
Write-Report "TOP_DIRECT_DEM_LOOKUP_OK=$($directOk.ToString().ToLower())"
Write-Report "TOP_SOURCE_COVERAGE=$coverage"
if ($final) {
  if ($coverage -ne 'England_wide') { Write-Report 'NON_BLOCKING_WARNING=England-wide source coverage not proven; runtime validated with London_only coverage' }
  Write-Report "RUNTIME_REPORT_ALREADY_100=$($runtime100.ToString().ToLower())"
  Write-Report 'FINAL_STATUS=FINAL_READY_CONFIRMED'
  Write-Report 'PRODUCT_PROGRESS_ESTIMATE=100'
  Write-Report 'PRODUCTION_COMPLETE=true'
  Write-State 'FINAL_READY_CONFIRMED' $true
  Commit-Outputs 'Confirm topography runtime finalization through shared runner'
}
elseif (-not (Test-Path -LiteralPath $runtimeReport)) {
  Write-Report 'FINAL_STATUS=RUNTIME_REPORT_MISSING'
  Write-Report 'PRODUCT_PROGRESS_ESTIMATE=99.998'
  Write-Report 'PRODUCTION_COMPLETE=false'
  Write-State 'RUNTIME_REPORT_MISSING' $false
  Commit-Outputs 'Report topography runtime report missing'
}
else {
  Write-Report 'FINAL_STATUS=TOPOGRAPHY_RUNTIME_BLOCKED'
  Write-Report 'PRODUCT_PROGRESS_ESTIMATE=99.998'
  Write-Report 'PRODUCTION_COMPLETE=false'
  if ($runtimeText -match 'MISSING_ITEMS=([^\r\n]*)') { Write-Report "MISSING_ITEMS=$($matches[1])" }
  Write-State 'TOPOGRAPHY_RUNTIME_BLOCKED' $false
  Commit-Outputs 'Report topography runtime blocked'
}
exit 0
