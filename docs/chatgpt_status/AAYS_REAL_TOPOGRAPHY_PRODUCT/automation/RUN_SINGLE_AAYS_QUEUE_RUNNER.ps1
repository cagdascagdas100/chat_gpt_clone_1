param(
  [string]$RepoRoot = "F:\chatgpt\AAYS_WORKTREES\aays-runner-v17-icon-work-20260603-232706",
  [string]$PageKey = "AAYS_REAL_TOPOGRAPHY_PRODUCT",
  [string]$Branch = "aays-runner-v17-icon-work-20260603-232706",
  [string]$BaseUrl = "http://127.0.0.1:8010",
  [int]$PollSeconds = 60,
  [switch]$Once,
  [switch]$Force
)

$ErrorActionPreference = "Stop"
$StatusRootRel = "docs/chatgpt_status/$PageKey"
$StatusRoot = Join-Path $RepoRoot ($StatusRootRel -replace '/', [IO.Path]::DirectorySeparatorChar)
$ReportDir = Join-Path $StatusRoot "reports"
$StatusDir = Join-Path $StatusRoot "status"
$HeartbeatDir = Join-Path $StatusRoot "heartbeat"
$RunnerOutDir = Join-Path $StatusRoot "runner_outputs"
$AutomationDir = Join-Path $StatusRoot "automation"
$StatePath = Join-Path $StatusRoot "single_runner_state.json"
$RunnerName = "single-aays-page-runner"

function Ensure-Dirs {
  New-Item -ItemType Directory -Force -Path $ReportDir,$StatusDir,$HeartbeatDir,$RunnerOutDir,$AutomationDir | Out-Null
}

function Write-Text([string]$Path, [string]$Text) {
  $parent = Split-Path -Parent $Path
  if ($parent) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
  Set-Content -Path $Path -Encoding UTF8 -Value $Text
}

function Run-Native([string]$Name, [scriptblock]$Block, [string]$LogPath) {
  Add-Content -Path $LogPath -Encoding UTF8 -Value "`n===== $Name START $(Get-Date -Format o) ====="
  $out = & $Block 2>&1 | Out-String
  $code = if ($null -ne $LASTEXITCODE) { [int]$LASTEXITCODE } else { 0 }
  Add-Content -Path $LogPath -Encoding UTF8 -Value $out
  Add-Content -Path $LogPath -Encoding UTF8 -Value "===== $Name END code=$code $(Get-Date -Format o) =====`n"
  return @{ ok = ($code -eq 0); code = $code; text = $out }
}

function Get-FileHashText([string]$Path) {
  if (!(Test-Path $Path)) { return "missing" }
  return (Get-FileHash -Algorithm SHA256 -Path $Path).Hash
}

function Load-State {
  if (!(Test-Path $StatePath)) { return @{} }
  try {
    $json = Get-Content $StatePath -Raw | ConvertFrom-Json
    $h = @{}
    $json.PSObject.Properties | ForEach-Object { $h[$_.Name] = $_.Value }
    return $h
  } catch { return @{} }
}

function Save-State([hashtable]$State) {
  Write-Text $StatePath ($State | ConvertTo-Json -Depth 5)
}

function Write-RunnerStatus([string]$Status, [string]$Detail, [string]$CurrentTask, [string]$AutomationScript, [string]$LogPath) {
  $ts = Get-Date -Format "yyyyMMdd_HHmmss"
  $body = @"
runner_name: $RunnerName
page_key: $PageKey
branch: $Branch
status: $Status
detail: $Detail
current_task: $CurrentTask
automation_script: $AutomationScript
log_path: $LogPath
timestamp: $ts
repo_root: $RepoRoot
"@
  Write-Text (Join-Path $StatusDir "single_runner_status_latest.md") $body
  Write-Text (Join-Path $HeartbeatDir "single_runner_heartbeat_latest.md") $body
}

function Resolve-AutomationFromTask([string]$TaskPath) {
  $text = Get-Content $TaskPath -Raw
  $match = [regex]::Match($text, 'active_automation_artifact\s*:\s*([^\r\n]+)')
  if (!$match.Success) { $match = [regex]::Match($text, '(docs/chatgpt_status/' + [regex]::Escape($PageKey) + '/automation/[^\s`"'']+\.ps1)') }
  if (!$match.Success -and $text -match '047|Distance Property Types|distance_property_types') {
    return Join-Path $AutomationDir "RUN_DISTANCE_047_SELF_CONTAINED_REPAIR.ps1"
  }
  if (!$match.Success) { return $null }
  $rel = $match.Groups[1].Value.Trim().Trim('`"').Trim("'")
  return Join-Path $RepoRoot ($rel -replace '/', [IO.Path]::DirectorySeparatorChar)
}

function Invoke-OnePoll {
  Ensure-Dirs
  if (!(Test-Path $RepoRoot)) { throw "RepoRoot not found: $RepoRoot" }
  Set-Location $RepoRoot
  $ts = Get-Date -Format "yyyyMMdd_HHmmss"
  $runnerLog = Join-Path $RunnerOutDir "single_runner_execution_$ts.txt"
  Write-Text $runnerLog "single runner started $ts`nrepo=$RepoRoot`nbranch=$Branch`npage=$PageKey"

  $fetch = Run-Native "git_fetch" { git fetch origin $Branch --prune } $runnerLog
  $current = (git rev-parse --abbrev-ref HEAD 2>$null).Trim()
  if ($current -ne $Branch) { Run-Native "git_checkout" { git checkout $Branch } $runnerLog | Out-Null }
  $pull = Run-Native "git_pull_rebase_autostash" { git pull --rebase --autostash origin $Branch } $runnerLog
  if (-not $fetch.ok -or -not $pull.ok) {
    Write-RunnerStatus "GIT_BLOCKED" "fetch_or_pull_failed" "" "" $runnerLog
    return
  }

  $CurrentTaskDir = Join-Path $StatusRoot "current-task"
  $task = Get-ChildItem -Path $CurrentTaskDir -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
  if (!$task) {
    Write-RunnerStatus "IDLE_NO_CURRENT_TASK" "no current-task file found" "" "" $runnerLog
    return
  }

  $automation = Resolve-AutomationFromTask $task.FullName
  if (!$automation -or !(Test-Path $automation)) {
    Write-RunnerStatus "TASK_BLOCKED_NO_AUTOMATION" "automation artifact missing" $task.FullName $automation $runnerLog
    return
  }

  $taskHash = (Get-FileHash -Algorithm SHA256 -Path $task.FullName).Hash
  $scriptHash = Get-FileHashText $automation
  $jobKey = "$($task.FullName)|$taskHash|$automation|$scriptHash"
  $state = Load-State
  if (-not $Force -and $state.ContainsKey('last_job_key') -and $state['last_job_key'] -eq $jobKey) {
    Write-RunnerStatus "IDLE_ALREADY_EXECUTED" "current task and automation hash already executed" $task.FullName $automation $runnerLog
    return
  }

  Write-RunnerStatus "RUNNING" "executing automation" $task.FullName $automation $runnerLog
  $run = Run-Native "run_automation" { powershell -ExecutionPolicy Bypass -File $automation -RepoRoot $RepoRoot -PageKey $PageKey -Branch $Branch -BaseUrl $BaseUrl } $runnerLog
  $state = @{ last_job_key = $jobKey; last_task = $task.FullName; last_automation = $automation; last_run_ts = $ts; last_exit_code = $run.code }
  Save-State $state

  Run-Native "git_add_runner_outputs" { git add "$StatusRootRel/reports" "$StatusRootRel/status" "$StatusRootRel/heartbeat" "$StatusRootRel/runner_outputs" "$StatusRootRel/single_runner_state.json" } $runnerLog | Out-Null
  Run-Native "git_commit_runner_outputs" { git commit -m "Run single AAYS page runner" } $runnerLog | Out-Null
  Run-Native "git_push_runner_outputs" { git push origin HEAD:$Branch } $runnerLog | Out-Null
  Write-RunnerStatus "RUN_COMPLETE" "automation_exit_code=$($run.code)" $task.FullName $automation $runnerLog
}

while ($true) {
  try { Invoke-OnePoll } catch {
    Ensure-Dirs
    $errTs = Get-Date -Format "yyyyMMdd_HHmmss"
    $errLog = Join-Path $RunnerOutDir "single_runner_error_$errTs.txt"
    Write-Text $errLog $_.Exception.ToString()
    Write-RunnerStatus "RUNNER_ERROR" $_.Exception.Message "" "" $errLog
  }
  if ($Once) { break }
  Start-Sleep -Seconds $PollSeconds
}
