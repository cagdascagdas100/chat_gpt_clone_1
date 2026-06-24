param(
  [string]$RepoRoot = 'C:\Users\cagda\Documents\GitHub\AAYS',
  [string]$BridgeRoot = $env:AAYS_BRIDGE_ROOT,
  [string]$FallbackBridgeRoot = 'F:\AAYS_GITHUB_BRIDGE_CLEAN2',
  [string]$PageKey = 'security_public_safety_low_credit_20260612'
)

$ErrorActionPreference = 'Stop'

function Write-Utf8NoBom {
  param([string]$Path, [string]$Text)
  $dir = Split-Path -Parent $Path
  if ($dir) { New-Item -ItemType Directory -Force $dir | Out-Null }
  $utf8 = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText($Path, $Text, $utf8)
}

function JsonEscape([string]$s) {
  if ($null -eq $s) { return '' }
  return ($s -replace '\\','\\' -replace '"','\"')
}

$ts = Get-Date -Format 'yyyyMMdd_HHmmss'
if ([string]::IsNullOrWhiteSpace($BridgeRoot)) { $BridgeRoot = $FallbackBridgeRoot }

$pageRoot = Join-Path $RepoRoot "docs\chatgpt_status\$PageKey"
$reportsDir = Join-Path $pageRoot 'reports'
$queueDir = Join-Path $pageRoot 'queue'
$statusDir = Join-Path $pageRoot 'status'
$runnerOutputsDir = Join-Path $pageRoot 'runner_outputs'
$heartbeatDir = Join-Path $pageRoot 'heartbeat'
$scriptPath = Join-Path $pageRoot 'automation\vrun.ps1'
$runnerBootstrap = Join-Path $RepoRoot 'tools\AAYS_CANONICAL_RUNNER_BOOTSTRAP_AND_REPORT_20260604_001.ps1'

foreach ($d in @($reportsDir,$queueDir,$statusDir,$runnerOutputsDir,$heartbeatDir)) {
  New-Item -ItemType Directory -Force $d | Out-Null
}

$bridgePending = Join-Path $BridgeRoot 'ai-queue\pending'
$bridgeRunning = Join-Path $BridgeRoot 'ai-queue\running'
$bridgeDone = Join-Path $BridgeRoot 'ai-queue\done'
$bridgeFailed = Join-Path $BridgeRoot 'ai-queue\failed'
foreach ($d in @($bridgePending,$bridgeRunning,$bridgeDone,$bridgeFailed)) {
  New-Item -ItemType Directory -Force $d | Out-Null
}

$taskId = "terrayield-050-security-single-runner-contract-alignment-$ts"
$taskFile = "$taskId.task.json"
$repoTask = Join-Path $queueDir $taskFile
$bridgeTask = Join-Path $bridgePending $taskFile
$resultPath = Join-Path $runnerOutputsDir "050_runner_output_$ts.log"
$repoResultPath = "docs/chatgpt_status/$PageKey/runner_outputs/050_runner_output_$ts.log"
$runnerApplyReport = "docs/chatgpt_status/$PageKey/reports/050_single_runner_apply_$ts.md"
$fieldContractReport = "docs/chatgpt_status/$PageKey/reports/050_field_contract_$ts.json"

$task = [ordered]@{
  task_id = $taskId
  page_key = $PageKey
  script_path = $scriptPath
  result_path = $resultPath
  repo_result_path = $repoResultPath
  status = 'pending'
  priority = 50
  db_write = $false
  ddl = $false
  migration = $false
  production_deploy = $false
  fake_data = $false
  expected_runner_report = $runnerApplyReport
  expected_field_contract = $fieldContractReport
}
$taskJson = $task | ConvertTo-Json -Depth 8
Write-Utf8NoBom -Path $repoTask -Text $taskJson
Copy-Item -LiteralPath $repoTask -Destination $bridgeTask -Force

$bootstrapStatus = 'not_run'
$bootstrapOutput = ''
try {
  if (Test-Path -LiteralPath $runnerBootstrap) {
    $bootstrapOutput = powershell -NoProfile -ExecutionPolicy Bypass -File $runnerBootstrap 2>&1 | Out-String
    $bootstrapStatus = 'ran'
  } else {
    $bootstrapStatus = 'missing_bootstrap_script'
  }
} catch {
  $bootstrapStatus = 'bootstrap_error'
  $bootstrapOutput = $_.Exception.Message
}

Start-Sleep -Seconds 45

$pendingExists = Test-Path -LiteralPath $bridgeTask
$runningExists = Test-Path -LiteralPath (Join-Path $bridgeRunning $taskFile)
$doneExists = Test-Path -LiteralPath (Join-Path $bridgeDone $taskFile)
$failedExists = Test-Path -LiteralPath (Join-Path $bridgeFailed $taskFile)
$outputExists = Test-Path -LiteralPath $resultPath
$applyExists = Test-Path -LiteralPath (Join-Path $reportsDir "050_single_runner_apply_$ts.md")
$fieldExists = Test-Path -LiteralPath (Join-Path $reportsDir "050_field_contract_$ts.json")

$pickup = 'not_proven'
if ($doneExists -or $failedExists -or $runningExists -or $outputExists -or $applyExists -or $fieldExists) { $pickup = 'proven_local_only' }
if ($doneExists -or $outputExists -or $applyExists -or $fieldExists) { $pickup = 'proven' }

$pushBlockerType = 'none'
$gitStatusBefore = ''
$gitCommitOutput = ''
$gitPushOutput = ''
$pushOk = $false
try {
  Push-Location $RepoRoot
  $branch = (git rev-parse --abbrev-ref HEAD 2>&1 | Out-String).Trim()
  $remote = (git remote get-url origin 2>&1 | Out-String).Trim()
  $gitStatusBefore = git status --short -- "docs/chatgpt_status/$PageKey" 2>&1 | Out-String
  if ($branch -ne 'main') {
    $pushBlockerType = 'wrong_branch'
  } elseif ($remote -notmatch 'cagdascagdas100/chat_gpt_clone_1') {
    $pushBlockerType = 'wrong_repo'
  } else {
    git add "docs/chatgpt_status/$PageKey/queue/$taskFile" | Out-Null
    # report is written below, then staged/committed/pushed after report creation
  }
} catch {
  $pushBlockerType = 'git_precheck_error'
  $gitCommitOutput = $_.Exception.Message
} finally {
  try { Pop-Location } catch {}
}

$reportPath = Join-Path $reportsDir "runner_push_chain_check_$ts.md"
$report = @"
# Runner Push Chain Check

page_key=$PageKey
task_id=$taskId
created_at=$ts
repo_root=$RepoRoot
bridge_root=$BridgeRoot
script_path=$scriptPath
repo_task=$repoTask
bridge_task=$bridgeTask
result_path=$resultPath

bootstrap_status=$bootstrapStatus
bootstrap_output=
````text
$bootstrapOutput
````

pending_exists=$pendingExists
running_exists=$runningExists
done_exists=$doneExists
failed_exists=$failedExists
runner_output_exists=$outputExists
single_runner_apply_exists=$applyExists
field_contract_exists=$fieldExists
runner_pickup=$pickup

push_precheck_blocker=$pushBlockerType
git_status_before=
````text
$gitStatusBefore
````

expected_next_report=docs/chatgpt_status/$PageKey/reports/050_single_runner_apply_*.md
expected_field_contract=docs/chatgpt_status/$PageKey/reports/050_field_contract_*.json
expected_runner_output=docs/chatgpt_status/$PageKey/runner_outputs/050_runner_output_*.log

final_ready=false
completion_percent=88
"@
Write-Utf8NoBom -Path $reportPath -Text $report

try {
  Push-Location $RepoRoot
  if ($pushBlockerType -eq 'none') {
    git add "docs/chatgpt_status/$PageKey/queue/$taskFile" | Out-Null
    git add "docs/chatgpt_status/$PageKey/reports/runner_push_chain_check_$ts.md" | Out-Null
    $gitCommitOutput = git commit -m "probe $PageKey runner push chain $ts" 2>&1 | Out-String
    $gitPushOutput = git push origin main 2>&1 | Out-String
    if ($LASTEXITCODE -eq 0) { $pushOk = $true }
  }
} catch {
  if ($pushBlockerType -eq 'none') { $pushBlockerType = 'git_commit_or_push_error' }
  $gitPushOutput = $_.Exception.Message
} finally {
  try { Pop-Location } catch {}
}

$finalReport = Get-Content -LiteralPath $reportPath -Raw
$finalReport += @"

git_commit_output=
````text
$gitCommitOutput
````

git_push_output=
````text
$gitPushOutput
````

runner_push=$pushOk
push_blocker_type=$pushBlockerType
"@
Write-Utf8NoBom -Path $reportPath -Text $finalReport

if (-not $pushOk) {
  try {
    Push-Location $RepoRoot
    git add "docs/chatgpt_status/$PageKey/reports/runner_push_chain_check_$ts.md" | Out-Null
    git commit -m "record $PageKey runner push chain blocker $ts" 2>&1 | Out-Null
    git push origin main 2>&1 | Out-Null
  } catch {
    Write-Host "PUSH_BLOCKER_REPORT_LOCAL_ONLY=$reportPath"
  } finally {
    try { Pop-Location } catch {}
  }
}

Write-Host "AAYS_050_BRIDGE_QUEUE_PUSH_CHAIN_PROBE_DONE"
Write-Host "report=$reportPath"
Write-Host "task=$repoTask"
Write-Host "bridge_task=$bridgeTask"
Write-Host "runner_pickup=$pickup"
Write-Host "runner_push=$pushOk"
Write-Host "push_blocker_type=$pushBlockerType"
