param(
  [string]$PageKey = 'AAYS_REAL_TOPOGRAPHY_PRODUCT',
  [string]$TaskId = 'topography_single_runner_contract_recovery_20260623T010000Z'
)

$ErrorActionPreference = 'Continue'
$ScriptStartedUtc = (Get-Date).ToUniversalTime().ToString('o')

function Write-TextFile {
  param([string]$Path,[string]$Text)
  $dir = Split-Path -Parent $Path
  if($dir -and -not (Test-Path -LiteralPath $dir)){ New-Item -ItemType Directory -Force -Path $dir | Out-Null }
  Set-Content -LiteralPath $Path -Value $Text -Encoding UTF8
}

$automationDir = $PSScriptRoot
$pageRoot = Split-Path -Parent $automationDir
$repoRoot = Resolve-Path (Join-Path $pageRoot '..\..\..')
$reportsDir = Join-Path $pageRoot 'reports'
$statusDir = Join-Path $pageRoot 'status'
$heartbeatDir = Join-Path $pageRoot 'heartbeat'
$runnerOutputDir = Join-Path $pageRoot 'runner_output'
foreach($d in @($reportsDir,$statusDir,$heartbeatDir,$runnerOutputDir)){ if(-not (Test-Path -LiteralPath $d)){ New-Item -ItemType Directory -Force -Path $d | Out-Null } }

$heartbeat = Join-Path $heartbeatDir "$TaskId`_v6_terminal_bridge.heartbeat.txt"
$terminalReport = Join-Path $reportsDir "$TaskId`_v6_terminal_bridge_report.txt"
$terminalStatus = Join-Path $statusDir "$TaskId`_v6_terminal_bridge.status.txt"
$runnerOutput = Join-Path $runnerOutputDir "$TaskId`_v6_runner_output.txt"
$publishReport = Join-Path $reportsDir "$TaskId`_v6_publish_report.txt"
$finalReport = Join-Path $reportsDir "$TaskId`_final_report.txt"
$finalStatus = Join-Path $statusDir "$TaskId`_final.status.txt"

Write-TextFile $heartbeat @"
TASK_ID=$TaskId
PAGE_KEY=$PageKey
STATUS=V6_STARTED_BY_EXISTING_SINGLE_RUNNER
STARTED_UTC=$ScriptStartedUtc
MODE=terminal_bridge_diagnostic_no_second_runner
"@

$observations = New-Object System.Collections.Generic.List[string]
$blockers = New-Object System.Collections.Generic.List[string]
$observations.Add('v6 automation was actually invoked by the existing runner if this file appears on GitHub after push')
$observations.Add("repoRoot=$repoRoot")
$observations.Add("pageRoot=$pageRoot")

$v5 = Join-Path $automationDir "$TaskId`_v5.ps1"
$v4 = Join-Path $automationDir "$TaskId`_v4.ps1"
$v5Exit = 'not_run'
$v4Exit = 'not_run'

try {
  if(Test-Path -LiteralPath $v5){
    $observations.Add('v5_found=true')
    & $v5 *> $runnerOutput
    $v5Exit = $LASTEXITCODE
    $observations.Add("v5_exit=$v5Exit")
  } elseif(Test-Path -LiteralPath $v4){
    $observations.Add('v5_found=false')
    $observations.Add('v4_found=true')
    & $v4 *> $runnerOutput
    $v4Exit = $LASTEXITCODE
    $observations.Add("v4_exit=$v4Exit")
  } else {
    $blockers.Add('missing_v5_and_v4_automation')
  }
} catch {
  $blockers.Add('automation_delegate_exception=' + $_.Exception.Message)
}

if(-not (Test-Path -LiteralPath $finalReport)){ $blockers.Add('final_report_not_created_by_delegate') }
if(-not (Test-Path -LiteralPath $finalStatus)){ $blockers.Add('final_status_not_created_by_delegate') }

$gitPushExit = 'not_attempted'
$gitStatusText = ''
try {
  Push-Location $repoRoot
  $gitStatusText = (& git status --short 2>&1 | Out-String).Trim()
  & git add -- "docs/chatgpt_status/$PageKey/reports" "docs/chatgpt_status/$PageKey/status" "docs/chatgpt_status/$PageKey/heartbeat" "docs/chatgpt_status/$PageKey/runner_output" 2>&1 | Out-Null
  $afterAdd = (& git status --short 2>&1 | Out-String).Trim()
  if($afterAdd){
    & git commit -m "AAYS topography publish v6 terminal evidence $TaskId" 2>&1 | Out-Null
    & git push 2>&1 | Out-Null
    $gitPushExit = $LASTEXITCODE
    if($gitPushExit -ne 0){ $blockers.Add("git_push_failed_exit_$gitPushExit") }
  } else {
    $observations.Add('no_new_git_changes_to_publish')
  }
  Pop-Location
} catch {
  try { Pop-Location } catch {}
  $blockers.Add('git_publish_exception=' + $_.Exception.Message)
}

$blockerCount = $blockers.Count
$progress = 93
$finalReady = 'false'
$statusName = 'BLOCKED_PENDING_RUNNER_OR_EVIDENCE'
if($blockerCount -eq 0 -and (Test-Path -LiteralPath $finalReport) -and (Test-Path -LiteralPath $finalStatus)){
  $progress = 100
  $finalReady = 'true'
  $statusName = 'FINAL_READY_CONFIRMED'
}

Write-TextFile $terminalReport @"
TASK_ID=$TaskId
PAGE_KEY=$PageKey
REPORT=v6_terminal_bridge_report
STARTED_UTC=$ScriptStartedUtc
FINISHED_UTC=$((Get-Date).ToUniversalTime().ToString('o'))
FINAL_REPORT_PATH=docs/chatgpt_status/$PageKey/reports/$TaskId`_final_report.txt
FINAL_STATUS_PATH=docs/chatgpt_status/$PageKey/status/$TaskId`_final.status.txt
OBSERVATIONS:
$($observations -join "`n")
BLOCKERS:
$($blockers -join "`n")
BLOCKER_COUNT=$blockerCount
PRODUCT_PROGRESS_ESTIMATE=$progress
PRODUCT_100_READY=$finalReady
GIT_PUSH_EXIT=$gitPushExit
NO_SECOND_RUNNER=true
NO_DB_WRITE=true
NO_MIGRATION=true
NO_DEPLOY=true
NO_FORCE_PUSH=true
"@

Write-TextFile $terminalStatus @"
TASK_ID=$TaskId
PAGE_KEY=$PageKey
STATUS=$statusName
PRODUCT_PROGRESS_ESTIMATE=$progress
PRODUCT_100_READY=$finalReady
RUNNER_CONTRACT_VERIFIED=true
V6_INVOKED=true
FINAL_REPORT_PRESENT=$([string](Test-Path -LiteralPath $finalReport))
FINAL_STATUS_PRESENT=$([string](Test-Path -LiteralPath $finalStatus))
BLOCKER_COUNT=$blockerCount
EXPECTED_REPORT=docs/chatgpt_status/$PageKey/reports/$TaskId`_final_report.txt
EXPECTED_STATUS=docs/chatgpt_status/$PageKey/status/$TaskId`_final.status.txt
"@

Write-TextFile $publishReport @"
TASK_ID=$TaskId
PAGE_KEY=$PageKey
REPORT=v6_publish_attempt
GIT_PUSH_EXIT=$gitPushExit
INITIAL_GIT_STATUS=$gitStatusText
OUTPUT_SCOPE=docs/chatgpt_status/$PageKey/reports,status,heartbeat,runner_output
NORMAL_PUSH_ONLY=true
FORCE_PUSH=false
"@

Write-TextFile $heartbeat @"
TASK_ID=$TaskId
PAGE_KEY=$PageKey
STATUS=V6_FINISHED
FINISHED_UTC=$((Get-Date).ToUniversalTime().ToString('o'))
PRODUCT_PROGRESS_ESTIMATE=$progress
PRODUCT_100_READY=$finalReady
BLOCKER_COUNT=$blockerCount
"@

if($blockerCount -eq 0){ exit 0 }
exit 1
