# AAYS_REAL_TOPOGRAPHY_PRODUCT
# TASK_ID=topography_single_runner_contract_recovery_20260623T010000Z
# MODE=existing single shared runner only
# PURPOSE=run v4 audit, then publish only this page-key evidence if local Git state allows a normal non-forced push
# SAFETY=no db write, no migration, no deploy, no force push, no extra runner process

$ErrorActionPreference = 'Continue'
$TaskId = 'topography_single_runner_contract_recovery_20260623T010000Z'
$PageKey = 'AAYS_REAL_TOPOGRAPHY_PRODUCT'
$StartedUtc = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')

$AutomationDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PageRoot = Split-Path -Parent $AutomationDir
$StatusRoot = Split-Path -Parent $PageRoot
$DocsRoot = Split-Path -Parent $StatusRoot
$RepoRoot = Split-Path -Parent $DocsRoot

$ReportsDir = Join-Path $PageRoot 'reports'
$StatusDir = Join-Path $PageRoot 'status'
$HeartbeatDir = Join-Path $PageRoot 'heartbeat'
$RunnerOutputDir = Join-Path $PageRoot 'runner_output'
foreach ($Dir in @($ReportsDir,$StatusDir,$HeartbeatDir,$RunnerOutputDir)) {
  if (-not (Test-Path -LiteralPath $Dir)) { New-Item -ItemType Directory -Force -Path $Dir | Out-Null }
}

function Write-TextFile {
  param([string]$Path,[string]$Text)
  $Parent = Split-Path -Parent $Path
  if ($Parent -and -not (Test-Path -LiteralPath $Parent)) { New-Item -ItemType Directory -Force -Path $Parent | Out-Null }
  Set-Content -LiteralPath $Path -Value $Text -Encoding UTF8
}
function Add-TextLine {
  param([string]$Path,[string]$Text)
  Add-Content -LiteralPath $Path -Value $Text -Encoding UTF8
}

$PublishReport = Join-Path $ReportsDir "$TaskId`_v5_publish_attempt.txt"
$PublishStatus = Join-Path $StatusDir "$TaskId`_v5_publish.status.txt"
$Heartbeat = Join-Path $HeartbeatDir "$TaskId`_v5.heartbeat.txt"
$RunnerOutput = Join-Path $RunnerOutputDir "$TaskId`_v5_output.txt"

Write-TextFile $Heartbeat "TASK_ID=$TaskId`nPAGE_KEY=$PageKey`nSTATUS=V5_STARTED`nSTARTED_UTC=$StartedUtc`nMODE=existing_single_runner_only"
Write-TextFile $RunnerOutput "TASK_ID=$TaskId`nPAGE_KEY=$PageKey`nSTATUS=V5_RUNNING`nSTARTED_UTC=$StartedUtc`nREPO_ROOT=$RepoRoot`nPAGE_ROOT=$PageRoot"

$v4 = Join-Path $AutomationDir "$TaskId`_v4.ps1"
$V4Exit = 999
if (Test-Path -LiteralPath $v4) {
  Add-TextLine $RunnerOutput "V5_STEP=invoke_v4_audit"
  & $v4
  $V4Exit = $LASTEXITCODE
  Add-TextLine $RunnerOutput "V4_EXIT_CODE=$V4Exit"
} else {
  Add-TextLine $RunnerOutput "V4_MISSING=$v4"
}

$PublishLines = New-Object System.Collections.Generic.List[string]
$PublishLines.Add("TASK_ID=$TaskId")
$PublishLines.Add("PAGE_KEY=$PageKey")
$PublishLines.Add('REPORT_KIND=v5_publish_attempt')
$PublishLines.Add("STARTED_UTC=$StartedUtc")
$PublishLines.Add("V4_EXIT_CODE=$V4Exit")
$PublishLines.Add('SAFETY=no_force_push_only_page_key_evidence_paths')

Push-Location $RepoRoot
try {
  $branch = (git branch --show-current 2>&1 | Out-String).Trim()
  $head = (git rev-parse HEAD 2>&1 | Out-String).Trim()
  $PublishLines.Add("CURRENT_BRANCH=$branch")
  $PublishLines.Add("HEAD=$head")
  if (-not $branch) {
    $PublishLines.Add('PUBLISH_STATUS=SKIPPED_DETACHED_HEAD')
  } else {
    git add -- "docs/chatgpt_status/$PageKey/reports" "docs/chatgpt_status/$PageKey/status" "docs/chatgpt_status/$PageKey/heartbeat" "docs/chatgpt_status/$PageKey/runner_output" 2>&1 | ForEach-Object { $PublishLines.Add("GIT_ADD=$_") }
    $diffCheck = (git diff --cached --name-only -- "docs/chatgpt_status/$PageKey" 2>&1 | Out-String).Trim()
    if (-not $diffCheck) {
      $PublishLines.Add('PUBLISH_STATUS=NO_STAGED_EVIDENCE_CHANGES')
    } else {
      $PublishLines.Add('STAGED_FILES_BEGIN')
      foreach ($line in ($diffCheck -split "`r?`n")) { if ($line) { $PublishLines.Add("STAGED_FILE=$line") } }
      $PublishLines.Add('STAGED_FILES_END')
      $commitMessage = "AAYS Topography runner evidence $TaskId"
      $commitOut = (git commit -m $commitMessage 2>&1 | Out-String).Trim()
      $PublishLines.Add('GIT_COMMIT_OUTPUT_BEGIN')
      $PublishLines.Add($commitOut)
      $PublishLines.Add('GIT_COMMIT_OUTPUT_END')
      $newHead = (git rev-parse HEAD 2>&1 | Out-String).Trim()
      $PublishLines.Add("NEW_HEAD=$newHead")
      $pushOut = (git push origin "HEAD:$branch" 2>&1 | Out-String).Trim()
      $PublishLines.Add('GIT_PUSH_OUTPUT_BEGIN')
      $PublishLines.Add($pushOut)
      $PublishLines.Add('GIT_PUSH_OUTPUT_END')
      if ($LASTEXITCODE -eq 0) { $PublishLines.Add('PUBLISH_STATUS=PUSHED_TO_GITHUB') }
      else { $PublishLines.Add('PUBLISH_STATUS=PUSH_FAILED_NON_FORCED') }
    }
  }
} catch {
  $PublishLines.Add("PUBLISH_STATUS=ERROR")
  $PublishLines.Add("ERROR=$($_.Exception.Message)")
} finally {
  Pop-Location
}

$EndedUtc = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
$PublishLines.Add("ENDED_UTC=$EndedUtc")
Write-TextFile $PublishReport ($PublishLines -join [Environment]::NewLine)

$FinalReport = Join-Path $ReportsDir "$TaskId`_final_report.txt"
$FinalStatus = Join-Path $StatusDir "$TaskId`_final.status.txt"
$finalReportExists = Test-Path -LiteralPath $FinalReport
$finalStatusExists = Test-Path -LiteralPath $FinalStatus
$statusValue = 'V5_FINISHED_WAIT_FOR_GITHUB_EVIDENCE'
$progress = '93'
if ($finalReportExists -and $finalStatusExists) {
  $fr = Get-Content -LiteralPath $FinalReport -Raw -ErrorAction SilentlyContinue
  if ($fr -match 'FINAL_STATUS=FINAL_READY_CONFIRMED' -and $fr -match 'PRODUCT_PROGRESS_ESTIMATE=100' -and $fr -match 'PRODUCTION_COMPLETE=true') {
    $statusValue = 'FINAL_READY_CONFIRMED'
    $progress = '100'
  }
}

Write-TextFile $PublishStatus @"
TASK_ID=$TaskId
PAGE_KEY=$PageKey
STATUS=$statusValue
PRODUCT_PROGRESS_ESTIMATE=$progress
PRODUCTION_COMPLETE=$([string]($statusValue -eq 'FINAL_READY_CONFIRMED')).ToLower()
FINAL_REPORT_LOCAL_EXISTS=$finalReportExists
FINAL_STATUS_LOCAL_EXISTS=$finalStatusExists
POWER_SHELL_REQUIRED_FROM_USER=false
EXPECTED_REPORT=docs/chatgpt_status/$PageKey/reports/$TaskId`_final_report.txt
EXPECTED_STATUS=docs/chatgpt_status/$PageKey/status/$TaskId`_final.status.txt
ENDED_UTC=$EndedUtc
"@
Write-TextFile $Heartbeat "TASK_ID=$TaskId`nPAGE_KEY=$PageKey`nSTATUS=V5_FINISHED`nENDED_UTC=$EndedUtc`nFINAL_REPORT_LOCAL_EXISTS=$finalReportExists`nFINAL_STATUS_LOCAL_EXISTS=$finalStatusExists"
Add-TextLine $RunnerOutput "V5_FINISHED STATUS=$statusValue PROGRESS=$progress ENDED_UTC=$EndedUtc"
exit 0
