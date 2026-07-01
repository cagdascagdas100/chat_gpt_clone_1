$ErrorActionPreference = 'Continue'

$TaskId = 'terrayield-046-runner-sync-recovery-then-accuracy-expansion'
$PageKey = 'aays1'
$StartedAt = (Get-Date).ToString('s')
$ScriptPath = $MyInvocation.MyCommand.Path
$AutomationRoot = Split-Path -Parent $ScriptPath
$PageRoot = Split-Path -Parent $AutomationRoot

function Find-RepoRoot([string]$StartPath) {
  $p = (Resolve-Path $StartPath).Path
  for ($i = 0; $i -lt 10; $i++) {
    if (Test-Path (Join-Path $p '.git')) { return $p }
    if (Test-Path (Join-Path $p 'docs\chatgpt_status')) { return $p }
    $parent = Split-Path -Parent $p
    if ([string]::IsNullOrWhiteSpace($parent) -or $parent -eq $p) { break }
    $p = $parent
  }
  if ($env:AAYS_REPO_ROOT -and (Test-Path $env:AAYS_REPO_ROOT)) { return (Resolve-Path $env:AAYS_REPO_ROOT).Path }
  return 'F:\chatgpt\chat_gpt_clone_1_main'
}

$RepoRoot = Find-RepoRoot $PageRoot
$BridgeRoot = if ($env:AAYS_BRIDGE_ROOT) { $env:AAYS_BRIDGE_ROOT } else { 'F:\AAYS_GITHUB_BRIDGE_CLEAN2' }
$BaseUrl = if ($env:AAYS_BASE_URL) { $env:AAYS_BASE_URL } else { 'http://127.0.0.1:8010' }

$Reports = Join-Path $PageRoot 'reports'
$Status = Join-Path $PageRoot 'status'
$Heartbeat = Join-Path $PageRoot 'heartbeat'
$RunnerOutputs = Join-Path $PageRoot 'runner_outputs'
$Queue = Join-Path $PageRoot 'queue'
$Child = Join-Path $PageRoot 'child_tasks'
New-Item -ItemType Directory -Force -Path $Reports,$Status,$Heartbeat,$RunnerOutputs,$Queue,$Child | Out-Null

function Write-Text([string]$Path, [string[]]$Lines) {
  $dir = Split-Path -Parent $Path
  if ($dir) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
  Set-Content -LiteralPath $Path -Encoding UTF8 -Value $Lines
}

function Add-SafeLine([System.Collections.Generic.List[string]]$Lines, [string]$Line) {
  [void]$Lines.Add($Line)
}

function Safe-Command([string]$Name, [scriptblock]$Block) {
  try {
    $out = & $Block 2>&1 | Out-String
    return ($out.Trim())
  } catch {
    return "$Name`_ERROR=$($_.Exception.Message)"
  }
}

$heartbeatFile = Join-Path $Heartbeat "$TaskId.running.heartbeat.txt"
Write-Text $heartbeatFile @(
  "TASK_ID=$TaskId",
  "PAGE_KEY=$PageKey",
  "STATUS=RUNNING_BY_SINGLE_SHARED_RUNNER",
  "STARTED_AT=$StartedAt",
  "SCRIPT_PATH=$ScriptPath",
  "REPO_ROOT=$RepoRoot",
  "BRIDGE_ROOT=$BridgeRoot",
  'db_write=false',
  'ddl=false',
  'migration=false',
  'production_deploy=false',
  'fake_data=false'
)

$evidence = New-Object System.Collections.Generic.List[string]
Add-SafeLine $evidence "PAGE_KEY=$PageKey"
Add-SafeLine $evidence "TASK_ID=$TaskId"
Add-SafeLine $evidence "REPORT_KIND=046_runner_sync_recovery_then_accuracy_expansion"
Add-SafeLine $evidence "STARTED_AT=$StartedAt"
Add-SafeLine $evidence "REPO_ROOT=$RepoRoot"
Add-SafeLine $evidence "BRIDGE_ROOT=$BridgeRoot"
Add-SafeLine $evidence "SCRIPT_PATH=$ScriptPath"
Add-SafeLine $evidence "BASE_URL=$BaseUrl"
Add-SafeLine $evidence 'SAFETY=db_write_false,ddl_false,migration_false,production_deploy_false,fake_data_false,new_runner_false'

# Repo and Git proof. Fetch only; no pull, no rebase, no force, no branch switch.
try {
  Push-Location $RepoRoot
  Add-SafeLine $evidence "GIT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>&1 | Out-String)".Trim()
  Add-SafeLine $evidence "GIT_HEAD=$(git rev-parse HEAD 2>&1 | Out-String)".Trim()
  Add-SafeLine $evidence "GIT_REMOTE_ORIGIN=$(git remote get-url origin 2>&1 | Out-String)".Trim()
  Add-SafeLine $evidence 'GIT_STATUS_SHORT_BEGIN'
  Add-SafeLine $evidence ((git status --short 2>&1 | Out-String).Trim())
  Add-SafeLine $evidence 'GIT_STATUS_SHORT_END'
  Add-SafeLine $evidence 'GIT_FETCH_OUTPUT_BEGIN'
  Add-SafeLine $evidence ((git fetch --prune origin 2>&1 | Out-String).Trim())
  Add-SafeLine $evidence 'GIT_FETCH_OUTPUT_END'
  $branch = (git rev-parse --abbrev-ref HEAD 2>&1 | Out-String).Trim()
  $head = (git rev-parse HEAD 2>&1 | Out-String).Trim()
  $remoteHead = (git rev-parse "origin/$branch" 2>&1 | Out-String).Trim()
  Add-SafeLine $evidence "REMOTE_HEAD_FOR_LOCAL_BRANCH=$remoteHead"
  if ($remoteHead -and $remoteHead -notmatch 'fatal') {
    $base = (git merge-base $branch "origin/$branch" 2>&1 | Out-String).Trim()
    Add-SafeLine $evidence "MERGE_BASE=$base"
    Add-SafeLine $evidence "AHEAD_BEHIND_LOCAL_REMOTE=$((git rev-list --left-right --count "$branch...origin/$branch" 2>&1 | Out-String).Trim())"
    if ($head -eq $remoteHead) { Add-SafeLine $evidence 'REMOTE_SYNC_STATUS=IN_SYNC' }
    elseif ($base -eq $remoteHead) { Add-SafeLine $evidence 'REMOTE_SYNC_STATUS=LOCAL_AHEAD_FAST_FORWARD_PUSH_POSSIBLE' }
    elseif ($base -eq $head) { Add-SafeLine $evidence 'REMOTE_SYNC_STATUS=LOCAL_BEHIND_PULL_REQUIRED' }
    else { Add-SafeLine $evidence 'REMOTE_SYNC_STATUS=DIVERGED_NON_FAST_FORWARD_RISK' }
  } else {
    Add-SafeLine $evidence 'REMOTE_SYNC_STATUS=REMOTE_BRANCH_NOT_FOUND_OR_UNREADABLE'
  }
  Pop-Location
} catch {
  Add-SafeLine $evidence "GIT_PROOF_ERROR=$($_.Exception.Message)"
  try { Pop-Location } catch {}
}

# Runner process and bridge evidence; read-only.
$runnerCount = 0
try {
  $runnerProcs = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
    ($_.CommandLine -like '*RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER.ps1*') -or
    ($_.CommandLine -like '*portable-runner*') -or
    ($_.CommandLine -like '*portable_queue_runner.ps1*') -or
    ($_.CommandLine -like '*ai-runner*') -or
    ($_.CommandLine -like '*ai-queue*')
  })
  $runnerCount = $runnerProcs.Count
  Add-SafeLine $evidence "RUNNER_PROCESS_COUNT=$runnerCount"
  foreach ($p in $runnerProcs) { Add-SafeLine $evidence "RUNNER_PROCESS=$($p.ProcessId)|$($p.CommandLine)" }
} catch {
  Add-SafeLine $evidence "RUNNER_PROCESS_SCAN_ERROR=$($_.Exception.Message)"
}

$probeRoots = @(
  $PageRoot,
  (Join-Path $RepoRoot 'docs\chatgpt_status'),
  $BridgeRoot,
  (Join-Path $BridgeRoot 'queue'),
  (Join-Path $BridgeRoot 'state'),
  (Join-Path $BridgeRoot 'logs'),
  (Join-Path $BridgeRoot 'results'),
  (Join-Path $BridgeRoot 'runner_outputs'),
  (Join-Path $BridgeRoot 'ai-tasks'),
  (Join-Path $BridgeRoot 'ai-results'),
  (Join-Path $BridgeRoot 'ai-heartbeat')
)
foreach ($root in $probeRoots) {
  Add-SafeLine $evidence "PATH_EXISTS[$root]=$(Test-Path -LiteralPath $root)"
}

$needles = @($TaskId, '046', '044', 'current-task', 'queue', 'heartbeat', 'final_ready', 'blockers', 'runner_outputs')
foreach ($root in $probeRoots | Where-Object { Test-Path -LiteralPath $_ }) {
  foreach ($needle in $needles) {
    try {
      $matches = @(Get-ChildItem -LiteralPath $root -Recurse -File -ErrorAction SilentlyContinue | Where-Object {
        $_.FullName -like "*$needle*" -or (($_.Length -lt 1048576) -and ((Get-Content -LiteralPath $_.FullName -Raw -ErrorAction SilentlyContinue) -like "*$needle*"))
      } | Select-Object -First 25)
      foreach ($m in $matches) { Add-SafeLine $evidence "EVIDENCE_MATCH[$needle]=$($m.FullName)" }
    } catch {
      Add-SafeLine $evidence "EVIDENCE_SCAN_ERROR[$root][$needle]=$($_.Exception.Message)"
    }
  }
}

# Endpoint health probe; read-only HTTP GET only.
$endpointReport = New-Object System.Collections.Generic.List[string]
Add-SafeLine $endpointReport "TASK_ID=$TaskId"
Add-SafeLine $endpointReport "BASE_URL=$BaseUrl"
$endpoints = @('/health', '/map/parcels?limit=5', '/map/listings?limit=5', '/map/sales-history/combined?limit=5')
foreach ($ep in $endpoints) {
  $url = "$BaseUrl$ep"
  $sw = [System.Diagnostics.Stopwatch]::StartNew()
  try {
    $resp = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 10 -Method GET
    $sw.Stop()
    Add-SafeLine $endpointReport "ENDPOINT[$ep]=HTTP_$([int]$resp.StatusCode)|ms=$([math]::Round($sw.Elapsed.TotalMilliseconds,1))|bytes=$([Text.Encoding]::UTF8.GetByteCount([string]$resp.Content))"
  } catch {
    $sw.Stop()
    Add-SafeLine $endpointReport "ENDPOINT[$ep]=ERR|ms=$([math]::Round($sw.Elapsed.TotalMilliseconds,1))|error=$($_.Exception.Message)"
  }
}
$endpointPath = Join-Path $Reports "$TaskId.endpoint_health_probe.txt"
Write-Text $endpointPath $endpointReport
Add-SafeLine $evidence "ENDPOINT_HEALTH_PROBE=$endpointPath"

# Red-flag quickscan; read-only.
$redFlags = @('fake_data', 'dummy contractor', 'mock contractor', 'FINAL_READY=true', 'completion_percent=100', 'PRODUCTION_COMPLETE=true')
$redReport = New-Object System.Collections.Generic.List[string]
Add-SafeLine $redReport "TASK_ID=$TaskId"
foreach ($flag in $redFlags) {
  $hits = @()
  foreach ($root in @($PageRoot, (Join-Path $RepoRoot 'docs\chatgpt_status')) | Where-Object { Test-Path -LiteralPath $_ }) {
    try {
      $hits += @(Get-ChildItem -LiteralPath $root -Recurse -File -ErrorAction SilentlyContinue | Where-Object {
        $_.Length -lt 1048576 -and ((Get-Content -LiteralPath $_.FullName -Raw -ErrorAction SilentlyContinue) -like "*$flag*")
      } | Select-Object -First 20)
    } catch {}
  }
  Add-SafeLine $redReport "REDFLAG[$flag]=$($hits.Count)"
  foreach ($h in $hits) { Add-SafeLine $redReport "REDFLAG_FILE[$flag]=$($h.FullName)" }
}
$redPath = Join-Path $Reports "$TaskId.red_flag_quickscan.txt"
Write-Text $redPath $redReport
Add-SafeLine $evidence "RED_FLAG_QUICKSCAN=$redPath"

# Child 044 request marker only; this does not start a new runner or spawn parallel runner processes.
$childRequest = Join-Path $Child 'terrayield-044-comprehensive-accuracy-expansion.child-request.json'
$childJson = @{
  parent_task_id = $TaskId
  child_task_id = 'terrayield-044-comprehensive-accuracy-expansion'
  page_key = $PageKey
  created_at = (Get-Date).ToString('s')
  mode = 'request_marker_only_no_new_runner_spawn'
  acceptance = @('source_accuracy_evidence', 'parcel_match_accuracy_evidence', 'operational_health_evidence', 'child_exit_code_or_blocker')
  safety = @('db_write_false', 'ddl_false', 'migration_false', 'production_deploy_false', 'fake_data_false')
} | ConvertTo-Json -Depth 6
Set-Content -LiteralPath $childRequest -Encoding UTF8 -Value $childJson
Add-SafeLine $evidence "CHILD_044_REQUEST_MARKER=$childRequest"
Add-SafeLine $evidence 'CHILD_044_STARTED_BY_THIS_SCRIPT=false'

# Determine guarded status. Do not mark ready without external runner evidence and child exit proof.
$blockers = New-Object System.Collections.Generic.List[string]
if ($runnerCount -eq 0) { [void]$blockers.Add('runner_process_not_detected_from_script_context') }
if (-not (Test-Path -LiteralPath $BridgeRoot)) { [void]$blockers.Add('missing_bridge_root') }
[void]$blockers.Add('missing_044_child_exit_code_or_completion_evidence')
[void]$blockers.Add('final_ready_requires_human_or_runner_verified_github_main_evidence')

$statusValue = 'IN_PROGRESS'
$completion = 52
if ($blockers.Count -gt 0) { $statusValue = 'BLOCKED'; $completion = 48 }

Add-SafeLine $evidence "STATUS=$statusValue"
Add-SafeLine $evidence "completion_percent=$completion"
Add-SafeLine $evidence 'final_ready=false'
foreach ($b in $blockers) { Add-SafeLine $evidence "BLOCKER=$b" }
Add-SafeLine $evidence 'next_action=Allow the existing single shared runner to process this script_path task, then rerun evidence collection and check child 044 exit proof. Do not start a second runner.'

$evidencePath = Join-Path $Reports "$TaskId.evidence_recovery_report.txt"
$statusPath = Join-Path $Status "$TaskId.status.txt"
$latestPath = Join-Path $RunnerOutputs "$TaskId.latest.txt"
Write-Text $evidencePath $evidence
Write-Text $statusPath @(
  "PAGE_KEY=$PageKey",
  "TASK_ID=$TaskId",
  "STATUS=$statusValue",
  "completion_percent=$completion",
  'final_ready=false',
  "runner_process_count=$runnerCount",
  "report=$evidencePath",
  "endpoint_report=$endpointPath",
  "red_flag_report=$redPath",
  "child_request=$childRequest",
  'db_write=false',
  'ddl=false',
  'migration=false',
  'production_deploy=false',
  'fake_data=false'
)
Write-Text $latestPath $evidence

# Safe report-only Git sync attempt. No code mutation, no DB, no force push.
try {
  Push-Location $RepoRoot
  $changed = (git status --short -- docs/chatgpt_status/$PageKey 2>&1 | Out-String).Trim()
  if ($changed) {
    git add "docs/chatgpt_status/$PageKey" | Out-Null
    git commit -m "AAYS 046 evidence recovery report" | Out-File -FilePath (Join-Path $Reports "$TaskId.git_commit_output.txt") -Encoding UTF8
    git push origin HEAD | Out-File -FilePath (Join-Path $Reports "$TaskId.git_push_output.txt") -Encoding UTF8
  } else {
    Set-Content -LiteralPath (Join-Path $Reports "$TaskId.git_sync_output.txt") -Encoding UTF8 -Value 'NO_REPORT_CHANGES_TO_COMMIT'
  }
  Pop-Location
} catch {
  try { Pop-Location } catch {}
  Set-Content -LiteralPath (Join-Path $Reports "$TaskId.git_sync_blocker.txt") -Encoding UTF8 -Value "GIT_SYNC_BLOCKER=$($_.Exception.Message)"
}

Get-Content -LiteralPath $statusPath
