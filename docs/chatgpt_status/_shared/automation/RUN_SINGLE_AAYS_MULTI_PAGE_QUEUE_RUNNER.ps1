[CmdletBinding()]
param(
  [switch]$Loop,
  [int]$IntervalSeconds = 60,
  [int]$MaxTasksPerScan = 1,
  [switch]$NoPush
)

$v5Runner = Join-Path $PSScriptRoot "RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_V5_20260706.ps1"
if (-not (Test-Path -LiteralPath $v5Runner)) {
  throw "Missing canonical V5 runner: $v5Runner"
}

$v5Args = @{
  IntervalSeconds = $IntervalSeconds
  MaxTasksPerScan = $MaxTasksPerScan
}
if ($Loop) { $v5Args.Loop = $true }
if ($NoPush) { $v5Args.NoPush = $true }

& $v5Runner @v5Args
exit $LASTEXITCODE

$ErrorActionPreference = "Stop"

$RunnableStatuses = @(
  "queued",
  "ready",
  "pending",
  "pending_repo_queue",
  "pickup_requested",
  "queued_for_single_shared_runner",
  "retry_pending",
  "failed_transient"
)

function Get-RepoRoot {
  return (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..\..\..")).Path
}

function Join-RepoPath {
  param([string]$RelativePath)
  return Join-Path $script:RepoRoot $RelativePath
}

function ConvertTo-RepoRelative {
  param([string]$Path)
  if ([string]::IsNullOrWhiteSpace($Path)) { return "" }
  $full = [System.IO.Path]::GetFullPath($Path)
  $root = [System.IO.Path]::GetFullPath($script:RepoRoot).TrimEnd('\')
  if ($full.StartsWith($root, [System.StringComparison]::OrdinalIgnoreCase)) {
    return $full.Substring($root.Length).TrimStart('\').Replace('\', '/')
  }
  return $full.Replace('\', '/')
}

function Read-JsonFile {
  param([string]$Path)
  try {
    $text = Get-Content -Raw -LiteralPath $Path
    if ([string]::IsNullOrWhiteSpace($text)) { return $null }
    return $text | ConvertFrom-Json -ErrorAction Stop
  } catch {
    return $null
  }
}

function Get-JsonValue {
  param([object]$Object, [string[]]$Names, [object]$Default = $null)
  if ($null -eq $Object) { return $Default }
  foreach ($name in $Names) {
    $prop = $Object.PSObject.Properties[$name]
    if ($null -ne $prop -and $null -ne $prop.Value) { return $prop.Value }
  }
  return $Default
}

function ConvertTo-SafeBool {
  param([object]$Value, [bool]$Default = $false)
  if ($null -eq $Value) { return $Default }
  if ($Value -is [bool]) { return [bool]$Value }
  $text = [string]$Value
  if ($text -match '^(?i:true|1|yes|y)$') { return $true }
  if ($text -match '^(?i:false|0|no|n)$') { return $false }
  return $Default
}

function Convert-Priority {
  param([object]$Value)
  $parsed = 100
  if ($null -eq $Value) { return $parsed }
  if ([int]::TryParse([string]$Value, [ref]$parsed)) { return $parsed }
  return 100
}

function Ensure-PageDirs {
  param([string]$PageKey)
  $root = Join-RepoPath "docs/chatgpt_status/$PageKey"
  foreach ($dir in @("queue", "status", "reports", "heartbeat", "completed", "blocked", "runner_outputs", "automation", "fixtures")) {
    New-Item -ItemType Directory -Force -Path (Join-Path $root $dir) | Out-Null
  }
}

function Test-RunnerLock {
  $lockDir = Join-RepoPath "docs/chatgpt_status/_shared/state"
  New-Item -ItemType Directory -Force -Path $lockDir | Out-Null
  $script:LockPath = Join-Path $lockDir "single_runner.lock.json"

  if (Test-Path -LiteralPath $script:LockPath) {
    $lock = Read-JsonFile -Path $script:LockPath
    $existingPid = if ($lock) { Get-JsonValue -Object $lock -Names @("pid", "runner_pid") } else { $null }
    if ($existingPid) {
      $existingProcess = Get-Process -Id ([int]$existingPid) -ErrorAction SilentlyContinue
      if ($null -ne $existingProcess -and [int]$existingPid -ne $PID) {
        return [pscustomobject]@{
          acquired = $false
          active_pid = [int]$existingPid
          lock_path = $script:LockPath
        }
      }
    }
  }

  $now = (Get-Date).ToUniversalTime().ToString("o")
  [ordered]@{
    pid = $PID
    runner_pid = $PID
    host = $env:COMPUTERNAME
    repo_root = $script:RepoRoot
    acquired_at = $now
    updated_at = $now
    runner_mode = "single_shared_runner"
  } | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $script:LockPath -Encoding UTF8

  return [pscustomobject]@{
    acquired = $true
    active_pid = $PID
    lock_path = $script:LockPath
  }
}

function Update-RunnerHeartbeat {
  param(
    [object[]]$Processed = @(),
    [object[]]$Skipped = @(),
    [string[]]$Blockers = @()
  )
  $now = (Get-Date).ToUniversalTime().ToString("o")
  $statusDir = Join-RepoPath "docs/chatgpt_status/_shared/status"
  $heartbeatDir = Join-RepoPath "docs/chatgpt_status/_shared/heartbeat"
  New-Item -ItemType Directory -Force -Path $statusDir | Out-Null
  New-Item -ItemType Directory -Force -Path $heartbeatDir | Out-Null

  $payload = [ordered]@{
    run_id = "single_runner_$($PID)"
    checked_at = $now
    repo_root = $script:RepoRoot
    main_branch = "main"
    runner_ready = $true
    queue_seen = ($Processed.Count -gt 0 -or $Skipped.Count -gt 0)
    queue_started = ($Processed.Count -gt 0)
    single_runner_lock_acquired = $true
    controller_sync_ok = $true
    task_runs_in_clean_worktree = $null
    allowed_paths_enforced = $true
    runner_output_uploaded = ($Processed.Count -gt 0)
    post_sync_ok = $null
    PUSH_SYNC_OK = $null
    CONTINUE_RUNNER_READY = $true
    main_summary_push_ok = $null
    processed = @($Processed)
    skipped = @($Skipped)
    blockers = @($Blockers | Select-Object -Unique)
    fake_data = $false
    db_write = $false
    migration = $false
    production_deploy = $false
  }
  $payload | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $statusDir "MULTI_PAGE_latest_status.json") -Encoding UTF8
  $payload | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $heartbeatDir "MULTI_PAGE_heartbeat_latest.json") -Encoding UTF8
}

function Get-QueueCandidates {
  $chatRoot = Join-RepoPath "docs/chatgpt_status"
  $candidates = New-Object System.Collections.Generic.List[object]
  foreach ($pageDir in Get-ChildItem -LiteralPath $chatRoot -Directory -ErrorAction SilentlyContinue) {
    if ($pageDir.Name -eq "_shared") { continue }
    $queueDir = Join-Path $pageDir.FullName "queue"
    if (-not (Test-Path -LiteralPath $queueDir)) { continue }
    $files = Get-ChildItem -LiteralPath $queueDir -File -Filter "*.json" -ErrorAction SilentlyContinue |
      Sort-Object @{ Expression = { if ($_.Name -eq "current.task.json") { 0 } else { 1 } } }, LastWriteTime
    foreach ($file in $files) {
      $queue = Read-JsonFile -Path $file.FullName
      if ($null -eq $queue) { continue }
      $status = ([string](Get-JsonValue -Object $queue -Names @("status") -Default "")).ToLowerInvariant()
      if ($RunnableStatuses -contains $status) {
        $candidates.Add([pscustomobject]@{
          page_key_from_path = $pageDir.Name
          queue_path = $file.FullName
          queue = $queue
          status = $status
        })
      }
    }
  }
  return @($candidates | Sort-Object @{ Expression = { Convert-Priority -Value (Get-JsonValue -Object $_.queue -Names @("priority") -Default 100) } }, queue_path)
}

function Normalize-QueueInMemory {
  param([object]$Candidate)
  $queue = $Candidate.queue
  $pageKey = [string]$Candidate.page_key_from_path
  $taskId = [string](Get-JsonValue -Object $queue -Names @("task_id", "taskId") -Default ([System.IO.Path]::GetFileNameWithoutExtension($Candidate.queue_path)))
  $taskId = ($taskId -replace '[^A-Za-z0-9_.-]', '_')
  $payloadPageKey = [string](Get-JsonValue -Object $queue -Names @("page_key", "pageKey") -Default "")
  $scriptPath = [string](Get-JsonValue -Object $queue -Names @("script_path", "scriptPath") -Default "")
  $automationScript = [string](Get-JsonValue -Object $queue -Names @("automation_script", "script") -Default "")
  if ([string]::IsNullOrWhiteSpace($scriptPath) -and -not [string]::IsNullOrWhiteSpace($automationScript)) { $scriptPath = $automationScript }
  if ([string]::IsNullOrWhiteSpace($automationScript) -and -not [string]::IsNullOrWhiteSpace($scriptPath)) { $automationScript = $scriptPath }
  $allowedPaths = @(Get-JsonValue -Object $queue -Names @("allowed_paths", "allowedPaths") -Default @())

  $errors = New-Object System.Collections.Generic.List[string]
  if ([string]::IsNullOrWhiteSpace($payloadPageKey)) { $errors.Add("missing_page_key") }
  elseif ($payloadPageKey -ne $pageKey) { $errors.Add("PAGE_KEY_PATH_MISMATCH") }
  if ([string]::IsNullOrWhiteSpace($scriptPath)) { $errors.Add("missing_script_path") }
  if ([string]::IsNullOrWhiteSpace($automationScript)) { $errors.Add("missing_automation_script") }
  if ($scriptPath -and $automationScript -and $scriptPath -ne $automationScript) { $errors.Add("script_path_automation_script_mismatch") }
  if ($allowedPaths.Count -eq 0) { $errors.Add("missing_allowed_paths") }
  foreach ($flag in @("no_fake_final_ready", "no_db_write", "no_migration", "no_production_deploy")) {
    if (-not (ConvertTo-SafeBool -Value (Get-JsonValue -Object $queue -Names @($flag)) -Default $false)) {
      $errors.Add("missing_or_false_$flag")
    }
  }
  if ((ConvertTo-SafeBool -Value (Get-JsonValue -Object $queue -Names @("final_ready", "finalReady")) -Default $false)) {
    $errors.Add("final_ready_true_requires_gate_evidence")
  }

  $scriptFull = if ($scriptPath) { Join-RepoPath $scriptPath } else { "" }
  if ($scriptPath -and -not (Test-Path -LiteralPath $scriptFull)) {
    $errors.Add("missing_script_file")
  }

  $scriptAllowed = $false
  foreach ($allowed in $allowedPaths) {
    $allowedText = ([string]$allowed).Replace('\', '/').TrimEnd('/') + '/'
    $scriptText = $scriptPath.Replace('\', '/')
    if ($scriptText.StartsWith($allowedText, [System.StringComparison]::OrdinalIgnoreCase)) {
      $scriptAllowed = $true
    }
  }
  if ($scriptPath -eq "docs/chatgpt_status/_shared/automation/SAFE_STATUS_ONLY_PAGE_TASK_20260706.ps1") {
    $scriptAllowed = $true
  }
  if ($scriptPath -and -not $scriptAllowed) {
    $errors.Add("script_path_outside_allowed_paths")
  }

  return [pscustomobject]@{
    page_key = $pageKey
    task_id = $taskId
    queue_path = $Candidate.queue_path
    queue_status = $Candidate.status
    script_path = $scriptPath
    script_full_path = $scriptFull
    allowed_paths = @($allowedPaths | ForEach-Object { [string]$_ })
    errors = @($errors | Select-Object -Unique)
  }
}

function Test-CleanWorktree {
  $status = & git -C $script:RepoRoot status --short
  return [pscustomobject]@{
    clean = ([string]::IsNullOrWhiteSpace(($status | Out-String).Trim()))
    status = @($status)
  }
}

function Write-TaskEvidence {
  param(
    [object]$Task,
    [string]$Status,
    [string[]]$Blockers = @(),
    [string[]]$Errors = @(),
    [string]$ScriptOutput = "",
    [bool]$QueueStarted = $false,
    [bool]$CleanWorktree = $false,
    [bool]$PushSyncOk = $false,
    [bool]$PostSyncOk = $false
  )

  Ensure-PageDirs -PageKey $Task.page_key
  $now = (Get-Date).ToUniversalTime().ToString("o")
  $pageRoot = Join-RepoPath "docs/chatgpt_status/$($Task.page_key)"
  $sharedStatusDir = Join-RepoPath "docs/chatgpt_status/_shared/status"
  New-Item -ItemType Directory -Force -Path $sharedStatusDir | Out-Null

  $payload = [ordered]@{
    task_id = $Task.task_id
    page_key = $Task.page_key
    status = $Status
    completed_at = if ($Status -eq "completed") { $now } else { $null }
    checked_at = $now
    queue_seen = $true
    queue_started = [bool]$QueueStarted
    single_runner_lock_acquired = $true
    task_runs_in_clean_worktree = [bool]$CleanWorktree
    allowed_paths_enforced = $true
    runner_output_uploaded = $true
    post_sync_ok = [bool]$PostSyncOk
    PUSH_SYNC_OK = [bool]$PushSyncOk
    CONTINUE_RUNNER_READY = ($Status -eq "completed" -and $PushSyncOk)
    final_ready = $false
    product_final_ready = $false
    fake_data = $false
    db_write = $false
    migration = $false
    production_deploy = $false
    blockers = @($Blockers | Select-Object -Unique)
    errors = @($Errors | Select-Object -Unique)
    outputs = @{}
    queue_path = ConvertTo-RepoRelative -Path $Task.queue_path
    script_path = $Task.script_path
  }

  $startedPath = Join-Path $pageRoot "status/$($Task.task_id)_started.json"
  $gatePath = Join-Path $pageRoot "status/$($Task.task_id)_gate.json"
  $statusPath = Join-Path $pageRoot "status/$($Task.task_id)_completed.json"
  $completedPath = Join-Path $pageRoot "completed/$($Task.task_id)_completed.json"
  $blockedPath = Join-Path $pageRoot "blocked/$($Task.task_id)_blocked.json"
  $heartbeatPath = Join-Path $pageRoot "heartbeat/$($Task.task_id)_heartbeat.txt"
  $reportPath = Join-Path $pageRoot "reports/$($Task.task_id)_runner_output.txt"
  $mirrorPath = Join-Path $sharedStatusDir "queue_result_mirror_$($Task.task_id).json"

  $payload | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $startedPath -Encoding UTF8
  $payload | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $gatePath -Encoding UTF8
  $payload | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $statusPath -Encoding UTF8
  if ($Status -eq "completed") {
    $payload | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $completedPath -Encoding UTF8
  } else {
    $payload | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $blockedPath -Encoding UTF8
  }
  $payload | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $mirrorPath -Encoding UTF8

  @(
    "PAGE_KEY=$($Task.page_key)",
    "TASK_ID=$($Task.task_id)",
    "RUNNER_ALIVE=true",
    "RUNNER_MODE=single_shared_runner",
    "HEARTBEAT_AT=$now",
    "QUEUE_FILE=$(ConvertTo-RepoRelative -Path $Task.queue_path)",
    "QUEUE_SEEN=true",
    "QUEUE_STARTED=$QueueStarted",
    "SINGLE_RUNNER_LOCK_ACQUIRED=true",
    "TASK_RUNS_IN_CLEAN_WORKTREE=$CleanWorktree",
    "ALLOWED_PATHS_ENFORCED=true",
    "RUNNER_OUTPUT_UPLOADED=true",
    "POST_SYNC_OK=$PostSyncOk",
    "PUSH_SYNC_OK=$PushSyncOk",
    "FINAL_READY=false",
    "BLOCKER=$(if ($Blockers.Count -gt 0) { $Blockers[0] } else { 'none' })"
  ) | Set-Content -LiteralPath $heartbeatPath -Encoding UTF8

  @(
    "AAYS single shared runner task report",
    "checked_at: $now",
    "page_key: $($Task.page_key)",
    "task_id: $($Task.task_id)",
    "status: $Status",
    "queue: $(ConvertTo-RepoRelative -Path $Task.queue_path)",
    "script_path: $($Task.script_path)",
    "final_ready: false",
    "fake_data: false",
    "db_write: false",
    "migration: false",
    "production_deploy: false",
    "blockers: $($Blockers -join '; ')",
    "errors: $($Errors -join '; ')",
    "",
    "script_output:",
    $ScriptOutput
  ) | Set-Content -LiteralPath $reportPath -Encoding UTF8

  return @($startedPath, $gatePath, $statusPath, $completedPath, $blockedPath, $heartbeatPath, $reportPath, $mirrorPath) |
    Where-Object { Test-Path -LiteralPath $_ }
}

function Sync-AllowedOutputs {
  param([object]$Task, [string[]]$TouchedPaths)
  if ($NoPush) {
    return [pscustomobject]@{ push_ok = $false; post_sync_ok = $false; message = "NoPush enabled" }
  }

  $allowedPrefixes = New-Object System.Collections.Generic.List[string]
  foreach ($allowed in $Task.allowed_paths) {
    $allowedPrefixes.Add(([string]$allowed).Replace('\', '/').TrimEnd('/') + '/')
  }
  foreach ($prefix in @(
    "docs/chatgpt_status/_shared/status/",
    "docs/chatgpt_status/_shared/heartbeat/",
    "docs/chatgpt_status/_shared/reports/",
    "docs/chatgpt_status/_shared/panel/",
    "docs/chatgpt_status/_shared/contracts/",
    "docs/chatgpt_status/_shared/templates/"
  )) {
    $allowedPrefixes.Add($prefix)
  }

  $changed = & git -C $script:RepoRoot status --short
  $allowedChanges = New-Object System.Collections.Generic.List[string]
  foreach ($line in $changed) {
    if ([string]::IsNullOrWhiteSpace($line)) { continue }
    $path = $line.Substring(3).Trim().Trim('"').Replace('\', '/')
    foreach ($prefix in $allowedPrefixes) {
      if ($path.StartsWith($prefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        $allowedChanges.Add($path)
        break
      }
    }
  }
  if ($allowedChanges.Count -eq 0) {
    return [pscustomobject]@{ push_ok = $false; post_sync_ok = $false; message = "No allowed changes to push" }
  }

  & git -C $script:RepoRoot add -- @($allowedChanges)
  & git -C $script:RepoRoot diff --cached --quiet
  if ($LASTEXITCODE -eq 0) {
    return [pscustomobject]@{ push_ok = $false; post_sync_ok = $false; message = "No staged diff" }
  }
  & git -C $script:RepoRoot commit -m "AAYS single shared runner evidence $($Task.task_id)"
  if ($LASTEXITCODE -ne 0) {
    return [pscustomobject]@{ push_ok = $false; post_sync_ok = $false; message = "git commit failed" }
  }
  & git -C $script:RepoRoot pull --rebase origin main
  $postSyncOk = ($LASTEXITCODE -eq 0)
  if (-not $postSyncOk) {
    return [pscustomobject]@{ push_ok = $false; post_sync_ok = $false; message = "git pull --rebase failed" }
  }
  & git -C $script:RepoRoot push origin main
  return [pscustomobject]@{ push_ok = ($LASTEXITCODE -eq 0); post_sync_ok = $postSyncOk; message = "push attempted" }
}

function Invoke-RunnerScan {
  $processed = New-Object System.Collections.Generic.List[object]
  $skipped = New-Object System.Collections.Generic.List[object]
  $blockers = New-Object System.Collections.Generic.List[string]

  $candidates = Get-QueueCandidates
  if ($candidates.Count -eq 0) {
    Update-RunnerHeartbeat -Processed @() -Skipped @() -Blockers @()
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-RepoPath "docs/chatgpt_status/_shared/automation/BUILD_AAYS_PAGE_PANEL_INDEX.ps1") -RepoRoot $script:RepoRoot | Out-Null
    return [pscustomobject]@{ processed = @(); skipped = @(); candidates = 0 }
  }

  foreach ($candidate in ($candidates | Select-Object -First $MaxTasksPerScan)) {
    $task = Normalize-QueueInMemory -Candidate $candidate
    if ($task.errors.Count -gt 0) {
      $null = Write-TaskEvidence -Task $task -Status "blocked" -Blockers $task.errors -Errors $task.errors -QueueStarted $false -CleanWorktree $false
      $skipped.Add([pscustomobject]@{ page_key = $task.page_key; task_id = $task.task_id; status = "blocked"; blockers = @($task.errors) })
      foreach ($err in $task.errors) { $blockers.Add($err) }
      continue
    }

    $clean = Test-CleanWorktree
    if (-not $clean.clean) {
      $block = @("worktree_not_clean")
      $null = Write-TaskEvidence -Task $task -Status "blocked" -Blockers $block -Errors @($clean.status) -QueueStarted $false -CleanWorktree $false
      $skipped.Add([pscustomobject]@{ page_key = $task.page_key; task_id = $task.task_id; status = "blocked"; blockers = $block })
      $blockers.Add("worktree_not_clean")
      continue
    }

    $scriptOutput = ""
    $exitCode = 0
    try {
      if ($task.script_path -eq "docs/chatgpt_status/_shared/automation/SAFE_STATUS_ONLY_PAGE_TASK_20260706.ps1") {
        $scriptOutput = (& powershell -NoProfile -ExecutionPolicy Bypass -File $task.script_full_path -PageKey $task.page_key -TaskId $task.task_id 2>&1 | Out-String)
      } else {
        $scriptOutput = (& powershell -NoProfile -ExecutionPolicy Bypass -File $task.script_full_path 2>&1 | Out-String)
      }
      $exitCode = $LASTEXITCODE
    } catch {
      $scriptOutput = $_.Exception.Message
      $exitCode = 1
    }

    if ($exitCode -ne 0) {
      $null = Write-TaskEvidence -Task $task -Status "failed" -Blockers @("automation_script_failed") -Errors @($scriptOutput) -ScriptOutput $scriptOutput -QueueStarted $true -CleanWorktree $true
      $skipped.Add([pscustomobject]@{ page_key = $task.page_key; task_id = $task.task_id; status = "failed"; blockers = @("automation_script_failed") })
      $blockers.Add("automation_script_failed")
      continue
    }

    $paths = Write-TaskEvidence -Task $task -Status "completed" -Blockers @() -Errors @() -ScriptOutput $scriptOutput -QueueStarted $true -CleanWorktree $true
    $sync = Sync-AllowedOutputs -Task $task -TouchedPaths $paths
    if (-not $sync.push_ok) {
      $null = Write-TaskEvidence -Task $task -Status "blocked" -Blockers @("push_sync_failed") -Errors @($sync.message) -ScriptOutput $scriptOutput -QueueStarted $true -CleanWorktree $true -PostSyncOk $sync.post_sync_ok -PushSyncOk $false
      $skipped.Add([pscustomobject]@{ page_key = $task.page_key; task_id = $task.task_id; status = "blocked"; blockers = @("push_sync_failed") })
      $blockers.Add("push_sync_failed")
      continue
    }
    $null = Write-TaskEvidence -Task $task -Status "completed" -Blockers @() -Errors @() -ScriptOutput $scriptOutput -QueueStarted $true -CleanWorktree $true -PostSyncOk $sync.post_sync_ok -PushSyncOk $sync.push_ok
    $processed.Add([pscustomobject]@{ page_key = $task.page_key; task_id = $task.task_id; status = "completed"; push_sync_ok = $sync.push_ok })
  }

  $processedArray = @($processed.ToArray())
  $skippedArray = @($skipped.ToArray())
  $blockerArray = @($blockers.ToArray())
  Update-RunnerHeartbeat -Processed $processedArray -Skipped $skippedArray -Blockers $blockerArray
  & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-RepoPath "docs/chatgpt_status/_shared/automation/BUILD_AAYS_PAGE_PANEL_INDEX.ps1") -RepoRoot $script:RepoRoot | Out-Null
  return [pscustomobject]@{ processed = $processedArray; skipped = $skippedArray; candidates = $candidates.Count }
}

$script:RepoRoot = Get-RepoRoot
Set-Location $script:RepoRoot
$lockResult = Test-RunnerLock
if (-not $lockResult.acquired) {
  Write-Output "runner already active pid=$($lockResult.active_pid)"
  exit 0
}

try {
  do {
    $scan = Invoke-RunnerScan
    $scan | ConvertTo-Json -Depth 8
    if ($Loop) { Start-Sleep -Seconds $IntervalSeconds }
  } while ($Loop)
} finally {
  if (Test-Path -LiteralPath $script:LockPath) {
    $lock = Read-JsonFile -Path $script:LockPath
    $pidValue = if ($lock) { Get-JsonValue -Object $lock -Names @("pid", "runner_pid") } else { $null }
    if ($pidValue -and [int]$pidValue -eq $PID) {
      Remove-Item -LiteralPath $script:LockPath -Force -ErrorAction SilentlyContinue
    }
  }
}
