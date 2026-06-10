$ErrorActionPreference = "Continue"
$ProgressPreference = "SilentlyContinue"

# TerraYield 051 contract inventory local kick v3 FEATURE-BRANCH SAFE
# Does NOT checkout/switch to main. It preserves the current local branch and writes/pushes reports from there.
# Does NOT run product changes.

$TaskId = "runner-contract-inventory-for-terrayield-051"
$ParentTaskId = "terrayield-051-london-only-pilot"
$StatusRootRel = "docs\chatgpt_status"
$OutRel = "docs\chatgpt_status\runner_outputs"
$ReportTxtName = "runner_contract_inventory_for_051_latest.txt"
$ReportJsonName = "runner_contract_inventory_for_051_latest.json"
$LatestName = "latest_output.json"
$Bridge = "C:\AAYS_GITHUB_BRIDGE_CLEAN2"
$Queue = Join-Path $Bridge "ai-queue"
$Runner = Join-Path $Bridge "ai-task-scripts\portable_queue_runner.ps1"

$LogLines = New-Object System.Collections.Generic.List[string]
function LogLine([string]$s) {
  $line = "{0} {1}" -f (Get-Date -Format o), $s
  $script:LogLines.Add($line) | Out-Null
  Write-Host $line
}
function SafeString([scriptblock]$Block) {
  try { return [string](& $Block) } catch { return "ERROR: $($_.Exception.Message)" }
}
function PathExists([string]$Path) {
  if ([string]::IsNullOrWhiteSpace($Path)) { return $false }
  try { return Test-Path -LiteralPath $Path } catch { return $false }
}
function AddCandidate([System.Collections.Generic.List[string]]$List, [string]$Path) {
  if (-not [string]::IsNullOrWhiteSpace($Path) -and -not $List.Contains($Path)) { $List.Add($Path) | Out-Null }
}
function Find-RepoRoot {
  $candidates = New-Object System.Collections.Generic.List[string]
  AddCandidate $candidates (SafeString { git rev-parse --show-toplevel 2>$null })
  AddCandidate $candidates (Get-Location).Path
  if ($PSScriptRoot) { AddCandidate $candidates $PSScriptRoot }
  if ($PSCommandPath) { AddCandidate $candidates (Split-Path -Parent $PSCommandPath) }
  AddCandidate $candidates "C:\Users\cagda\Documents\GitHub\AAYS"
  AddCandidate $candidates "C:\Users\cagda\Documents\GitHub\chat_gpt_clone_1"
  foreach ($start in @($candidates)) {
    if ([string]::IsNullOrWhiteSpace($start) -or $start.StartsWith("ERROR:")) { continue }
    $dir = $null
    try { $dir = (Resolve-Path -LiteralPath $start -ErrorAction Stop).Path } catch { continue }
    for ($i = 0; $i -lt 12; $i++) {
      if ((PathExists (Join-Path $dir ".git")) -and (PathExists (Join-Path $dir "$StatusRootRel\current-task.txt"))) { return $dir }
      $parent = Split-Path -Parent $dir
      if ([string]::IsNullOrWhiteSpace($parent) -or $parent -eq $dir) { break }
      $dir = $parent
    }
  }
  return $null
}
function EnsureDir([string]$Path) {
  try { if (-not (PathExists $Path)) { New-Item -ItemType Directory -Force -Path $Path | Out-Null }; return $true }
  catch { LogLine "DIR_CREATE_FAILED path=$Path error=$($_.Exception.Message)"; return $false }
}
function Run-Git([string]$Args) {
  try {
    $out = cmd /c "git $Args 2>&1"
    foreach ($l in $out) { LogLine "git $Args :: $l" }
    return $LASTEXITCODE
  } catch { LogLine "GIT_CMD_EXCEPTION args=$Args error=$($_.Exception.Message)"; return 999 }
}
function Write-Reports([string]$Repo, [hashtable]$Extra) {
  $outDir = Join-Path $Repo $OutRel
  EnsureDir $outDir | Out-Null
  $txt = Join-Path $outDir $ReportTxtName
  $json = Join-Path $outDir $ReportJsonName
  $latest = Join-Path $outDir $LatestName

  $obj = [ordered]@{
    task_id=$TaskId
    parent_task_id=$ParentTaskId
    status="contract_inventory_written_by_local_powershell_v3_feature_safe"
    overall_progress_percent=30
    current_branch=$Extra.current_branch
    repo=$Repo
    bridge=$Bridge
    queue=$Queue
    runner=$Runner
    repo_exists=(PathExists $Repo)
    repo_git_exists=(PathExists (Join-Path $Repo ".git"))
    current_task_exists=(PathExists (Join-Path $Repo "$StatusRootRel\current-task.txt"))
    bridge_exists=(PathExists $Bridge)
    queue_exists=(PathExists $Queue)
    runner_exists=(PathExists $Runner)
    runner_process_seen_before=$Extra.runner_process_seen_before
    runner_process_seen_after=$Extra.runner_process_seen_after
    product_changes_run=$false
    powershell_output_copied_to_github=$true
    script_version="v3_feature_branch_safe_no_main_checkout"
    timestamp=(Get-Date -Format o)
  }
  try { $obj | ConvertTo-Json -Depth 10 | Set-Content -Encoding UTF8 -Path $json } catch { LogLine "JSON_REPORT_WRITE_FAILED $($_.Exception.Message)" }

  $latestObj = [ordered]@{
    task_id=$TaskId
    parent_task_id=$ParentTaskId
    status="contract_inventory_available"
    overall_progress_percent=30
    phase="runner_contract_inventory_written_to_github_v3_feature_safe"
    current_branch=$Extra.current_branch
    next_chatgpt_action="read_contract_inventory_and_resume_terrayield_051_london_only_pilot"
    manual_powershell_required_now=$false
    timestamp=(Get-Date -Format o)
  }
  try { $latestObj | ConvertTo-Json -Depth 10 | Set-Content -Encoding UTF8 -Path $latest } catch { LogLine "LATEST_OUTPUT_WRITE_FAILED $($_.Exception.Message)" }
  try { $script:LogLines | Set-Content -Encoding UTF8 -Path $txt } catch { Write-Host "FAILED_TO_WRITE_TXT_REPORT $($_.Exception.Message)" }
}

LogLine "=== RUNNER CONTRACT INVENTORY 051 LOCAL KICK V3 FEATURE-SAFE START ==="
LogLine "PSCommandPath=$PSCommandPath"
LogLine "PSScriptRoot=$PSScriptRoot"
LogLine "cwd=$((Get-Location).Path)"

$repo = Find-RepoRoot
if (-not $repo) {
  LogLine "REPO_ROOT_NOT_FOUND. Cannot safely write GitHub report."
  $fallback = Join-Path $env:TEMP "runner_contract_inventory_for_051_repo_not_found.txt"
  try { $LogLines | Set-Content -Encoding UTF8 -Path $fallback; Write-Host "LOCAL_DIAGNOSTIC_WRITTEN=$fallback" } catch {}
  exit 2
}
Set-Location $repo
LogLine "repo=$repo"

$currentBranch = SafeString { git rev-parse --abbrev-ref HEAD 2>$null }
if ([string]::IsNullOrWhiteSpace($currentBranch) -or $currentBranch.StartsWith("ERROR:")) { $currentBranch = "feature/terrayield-aays-integration" }
LogLine "current_branch=$currentBranch"

$outDir = Join-Path $repo $OutRel
EnsureDir $outDir | Out-Null

LogLine "=== GIT STATUS / FETCH CURRENT BRANCH ONLY ==="
Run-Git "status --short" | Out-Null
Run-Git "fetch origin $currentBranch" | Out-Null
# Intentionally no checkout main and no pull --rebase main. Local tree is dirty; switching branches is the blocker.

LogLine "=== PATH CHECK ==="
LogLine "repo_exists=$(PathExists $repo)"
LogLine "repo_git_exists=$(PathExists (Join-Path $repo '.git'))"
LogLine "current_task_exists=$(PathExists (Join-Path $repo "$StatusRootRel\current-task.txt"))"
LogLine "bridge_exists=$(PathExists $Bridge)"
LogLine "queue_exists=$(PathExists $Queue)"
LogLine "runner_exists=$(PathExists $Runner)"

if (PathExists "F:\") {
  $froot = "F:\AAYS_GITHUB_WORK\terrayield-051-contract-inventory"
  EnsureDir $froot | Out-Null
  LogLine "froot=$froot froot_exists=$(PathExists $froot)"
} else {
  LogLine "F_DRIVE_MISSING continuing_without_froot"
}

LogLine "=== RUNNER PROCESS SNAPSHOT BEFORE ==="
$procs = @()
try {
  $procs = @(Get-CimInstance Win32_Process -ErrorAction Stop | Where-Object { $_.CommandLine -match "portable_queue_runner.ps1|AAYS_GITHUB_BRIDGE_CLEAN2|ai-queue" } | Select-Object ProcessId,CommandLine)
  if ($procs.Count -gt 0) { foreach ($p in $procs) { LogLine "PROCESS_BEFORE pid=$($p.ProcessId) cmd=$($p.CommandLine)" } } else { LogLine "NO_MATCHING_RUNNER_PROCESS_FOUND_BEFORE" }
} catch { LogLine "PROCESS_SNAPSHOT_BEFORE_FAILED $($_.Exception.Message)" }

LogLine "=== QUEUE SNAPSHOT ==="
if (PathExists $Queue) {
  try {
    $items = @(Get-ChildItem $Queue -Force -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 30 Name,Length,LastWriteTime)
    if ($items.Count -eq 0) { LogLine "QUEUE_EMPTY" }
    foreach ($it in $items) { LogLine "QUEUE_ITEM name=$($it.Name) length=$($it.Length) lastwrite=$($it.LastWriteTime)" }
  } catch { LogLine "QUEUE_SNAPSHOT_FAILED $($_.Exception.Message)" }
} else { LogLine "QUEUE_PATH_MISSING" }

$runnerAlreadyRunning = [bool]($procs.Count -gt 0)
if (-not $runnerAlreadyRunning -and (PathExists $Runner)) {
  LogLine "STARTING_SINGLE_CANONICAL_RUNNER"
  try { Start-Process powershell -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$Runner`"" -WindowStyle Normal; Start-Sleep -Seconds 10 }
  catch { LogLine "RUNNER_START_FAILED $($_.Exception.Message)" }
} else { LogLine "RUNNER_START_SKIPPED runnerAlreadyRunning=$runnerAlreadyRunning runnerExists=$(PathExists $Runner)" }

LogLine "=== RUNNER PROCESS SNAPSHOT AFTER ==="
$procsAfter = @()
try {
  $procsAfter = @(Get-CimInstance Win32_Process -ErrorAction Stop | Where-Object { $_.CommandLine -match "portable_queue_runner.ps1|AAYS_GITHUB_BRIDGE_CLEAN2|ai-queue" } | Select-Object ProcessId,CommandLine)
  if ($procsAfter.Count -gt 0) { foreach ($p in $procsAfter) { LogLine "PROCESS_AFTER pid=$($p.ProcessId) cmd=$($p.CommandLine)" } } else { LogLine "NO_MATCHING_RUNNER_PROCESS_FOUND_AFTER" }
} catch { LogLine "PROCESS_SNAPSHOT_AFTER_FAILED $($_.Exception.Message)" }

Write-Reports -Repo $repo -Extra @{ current_branch=$currentBranch; runner_process_seen_before=$runnerAlreadyRunning; runner_process_seen_after=[bool]($procsAfter.Count -gt 0) }

LogLine "=== GIT COMMIT/PUSH CURRENT BRANCH ONLY ==="
Run-Git "add $OutRel/$ReportTxtName $OutRel/$ReportJsonName $OutRel/$LatestName" | Out-Null
$commitExit = Run-Git "commit -m `"Add runner contract inventory for TerraYield 051 v3 feature-safe`""
if ($commitExit -ne 0) { LogLine "COMMIT_NONZERO exit=$commitExit maybe_no_changes_or_git_config_issue" }
$pushExit = Run-Git "push origin $currentBranch"
if ($pushExit -ne 0) { LogLine "PUSH_NONZERO exit=$pushExit" }

try { $script:LogLines | Set-Content -Encoding UTF8 -Path (Join-Path $outDir $ReportTxtName) } catch {}
LogLine "=== RUNNER CONTRACT INVENTORY 051 LOCAL KICK V3 FEATURE-SAFE END ==="
exit 0
