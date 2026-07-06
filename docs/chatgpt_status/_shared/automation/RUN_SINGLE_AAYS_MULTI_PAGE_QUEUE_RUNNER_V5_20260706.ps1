[CmdletBinding()]
param(
  [switch]$Loop,
  [int]$IntervalSeconds = 60,
  [int]$MaxTasksPerScan = 1,
  [int]$MaxTasks = 0,
  [string]$RepoRoot = "",
  [string]$RepoFullName = "cagdascagdas100/chat_gpt_clone_1",
  [string]$MainBranch = "",
  [string]$WorkRoot = "C:\AAYS_WT",
  [int]$StaleMinutes = 15,
  [switch]$NoPush,
  [switch]$ScanOnly
)

$ErrorActionPreference = "Stop"
if ($MaxTasks -gt 0) { $MaxTasksPerScan = $MaxTasks }
$RunnableStatuses = @("queued","ready","pending","pending_repo_queue","pickup_requested","queued_for_single_shared_runner","retry_pending","failed_transient")

function Now-Utc { (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ") }
function Safe-Name([string]$Value) { (($Value -replace '[^A-Za-z0-9_.-]', '_').Trim('_')) }
function Rel([string]$Path) { (($Path -replace '\\','/').TrimStart('/')) }
function Ensure-Dir([string]$Path) { if ($Path -and -not (Test-Path -LiteralPath $Path)) { New-Item -ItemType Directory -Force -Path $Path | Out-Null } }
function Write-Utf8([string]$Path, [string]$Content) { Ensure-Dir (Split-Path -Parent $Path); [System.IO.File]::WriteAllText($Path, $Content, [System.Text.UTF8Encoding]::new($false)) }
function To-JsonText([object]$Obj) { $Obj | ConvertTo-Json -Depth 80 }
function Get-Prop([object]$Obj, [string]$Name) { if ($null -eq $Obj) { return $null }; $p = $Obj.PSObject.Properties[$Name]; if ($p) { return $p.Value }; return $null }
function Add-Blocker([string]$Code) { if ($Code -and -not ($script:Summary.blockers -contains $Code)) { $script:Summary.blockers += $Code } }

function Invoke-Git {
  param([Parameter(Mandatory=$true)][string]$Cwd,[Parameter(ValueFromRemainingArguments=$true)][string[]]$Args)
  if ($null -eq $Args -or $Args.Count -eq 0) { throw "BLOCKED_BARE_GIT_USAGE" }
  Ensure-Dir (Split-Path -Parent $script:GitLogPath)
  Add-Content -LiteralPath $script:GitLogPath -Encoding UTF8 -Value ("[{0}] cwd={1} git {2}" -f (Now-Utc), $Cwd, ($Args -join ' '))
  Push-Location -LiteralPath $Cwd
  $old = $ErrorActionPreference
  try {
    $ErrorActionPreference = "Continue"
    $out = & git @Args 2>&1
    $code = $LASTEXITCODE
    return [pscustomobject]@{ code=$code; output=(($out | Out-String).TrimEnd()); args=$Args }
  } finally { $ErrorActionPreference = $old; Pop-Location }
}
function Git-Ok([object]$Result,[string]$Code) { if ($Result.code -ne 0) { throw ($Code + ": " + $Result.output) } }

function Get-RepoRoot {
  $candidates = @()
  if ($RepoRoot) { $candidates += $RepoRoot }
  $candidates += (Join-Path $PSScriptRoot "..\..\..\..")
  $candidates += "C:\AAYS_WT\AAYS_REPAIR_20260706_1738"
  $candidates += "C:\Users\cagda\Documents\GitHub\AAYS"
  $candidates += "F:\chatgpt\chat_gpt_clone_1_main"
  foreach ($c in $candidates) {
    $r = Resolve-Path -LiteralPath $c -ErrorAction SilentlyContinue
    if ($r -and (Test-Path -LiteralPath (Join-Path $r.Path ".git")) -and (Test-Path -LiteralPath (Join-Path $r.Path "docs/chatgpt_status/_shared"))) { return $r.Path }
  }
  throw "AAYS repo root not found. Pass -RepoRoot."
}
function Get-Branch([string]$Root) {
  $r = Invoke-Git $Root rev-parse --abbrev-ref HEAD
  Git-Ok $r "CURRENT_BRANCH_FAILED"
  $b = ($r.output -split "\r?\n" | Select-Object -First 1).Trim()
  if (-not $b -or $b -eq "HEAD") { throw "CURRENT_BRANCH_DETACHED" }
  return $b
}
function Dirty-Paths([string]$Root) {
  $r = Invoke-Git $Root status --porcelain
  Git-Ok $r "STATUS_FAILED"
  $paths = @()
  foreach ($line in @($r.output -split "\r?\n" | Where-Object { $_ })) {
    if ($line.Length -lt 4) { continue }
    $p = $line.Substring(3).Trim().Trim('"')
    if ($p -match " -> ") { $p = ($p -split " -> ")[-1] }
    $paths += (Rel $p)
  }
  return @($paths)
}
function Is-Runtime([string]$Path) {
  $p = Rel $Path
  return ($p.StartsWith("docs/chatgpt_status/_shared/status/") -or $p.StartsWith("docs/chatgpt_status/_shared/heartbeat/") -or $p.StartsWith("docs/chatgpt_status/_shared/logs/") -or $p.StartsWith("docs/chatgpt_status/_shared/reports/MULTI_PAGE_runner_output_V5_") -or $p.StartsWith("docs/chatgpt_status/_shared/runner_lock/"))
}
function Path-Allowed([string]$Path,[string[]]$Allowed) {
  $p = (Rel $Path).TrimEnd('/')
  foreach ($a in $Allowed) { $z=(Rel $a).TrimEnd('/'); if ($p -eq $z -or $p.StartsWith($z + "/")) { return $true } }
  return $false
}
function Normalize-Allowed([object]$Value,[string]$Page) {
  $items = @()
  if ($null -ne $Value) { if ($Value -is [System.Array]) { $items=@($Value) } else { $items=@(([string]$Value) -split '[,;]') } }
  $items += @("docs/chatgpt_status/$Page/**","docs/chatgpt_status/_shared/status/**","docs/chatgpt_status/_shared/heartbeat/**","docs/chatgpt_status/_shared/logs/**","docs/chatgpt_status/_shared/reports/**")
  return @($items | ForEach-Object { $x=Rel ([string]$_); $x=$x -replace '/\*\*$',''; $x=$x -replace '/\*$',''; $x.TrimEnd('/') } | Where-Object { $_ } | Select-Object -Unique)
}
function Stage-Allowed([string]$Root,[string[]]$Allowed) {
  $changed = @(Dirty-Paths $Root)
  $bad = @($changed | Where-Object { -not (Path-Allowed $_ $Allowed) })
  if ($bad.Count -gt 0) { throw ("BLOCKED_UNSCOPED_CHANGES: " + ($bad -join ',')) }
  foreach ($p in $changed) { Git-Ok (Invoke-Git $Root add -- $p) "ADD_FAILED" }
  return $changed
}
function Read-Queue([System.IO.FileInfo]$File) {
  $raw = Get-Content -LiteralPath $File.FullName -Raw
  if ($File.Extension -ieq ".json") { return ($raw | ConvertFrom-Json) }
  $map=[ordered]@{}
  foreach ($line in ($raw -split "`r?`n")) { $t=$line.Trim(); if (-not $t -or $t.StartsWith('#') -or $t -notmatch '=') { continue }; $i=$t.IndexOf('='); $map[$t.Substring(0,$i).Trim()]=$t.Substring($i+1).Trim() }
  return [pscustomobject]$map
}
function Parse-Queue([System.IO.FileInfo]$File) {
  $rel = Rel ($File.FullName.Substring($script:RepoRoot.Length).TrimStart('\','/'))
  if ($rel -notmatch '^docs/chatgpt_status/([^/]+)/queue/[^/]+$') { return [pscustomobject]@{ valid=$false; queue_rel=$rel; reason="bad_path" } }
  $pageFromPath=$Matches[1]
  $data=Read-Queue $File
  $page=[string](Get-Prop $data "page_key"); if (-not $page) { $page=$pageFromPath }
  $taskId=[string](Get-Prop $data "task_id"); if (-not $taskId) { $taskId=[System.IO.Path]::GetFileNameWithoutExtension($File.Name) }
  $status=[string](Get-Prop $data "status"); if (-not $status) { $status="queued" }
  $scriptPath=[string](Get-Prop $data "script_path"); if (-not $scriptPath) { $scriptPath=[string](Get-Prop $data "automation_script") }
  $priority=1000; $pr=Get-Prop $data "priority"; if ($null -ne $pr) { [void][int]::TryParse(([string]$pr), [ref]$priority) }
  $errors=@(); if ($page -ne $pageFromPath) { $errors += "PAGE_KEY_PATH_MISMATCH" }; if (-not $scriptPath) { $errors += "MISSING_SCRIPT_PATH" }
  return [pscustomobject]@{ valid=($errors.Count -eq 0); errors=$errors; page_key=$page; task_id=(Safe-Name $taskId); status_norm=$status.Trim().ToLowerInvariant(); script_path=$scriptPath; allowed_paths=(Normalize-Allowed (Get-Prop $data "allowed_paths") $page); queue_rel=$rel; priority=$priority; data=$data }
}
function Resolve-Script([string]$ScriptPath) {
  $p=$ScriptPath -replace '/', '\'
  if ([System.IO.Path]::IsPathRooted($p)) {
    $full=[System.IO.Path]::GetFullPath($p)
    $roots=@([System.IO.Path]::GetFullPath($script:RepoRoot).TrimEnd('\'),"C:\Users\cagda\Documents\GitHub\AAYS","C:\AAYS_WT\AAYS_REPAIR_20260706_1738","F:\chatgpt\chat_gpt_clone_1_main","F:\chatgpt\chat_gpt_clone_1_main_fresh")
    foreach ($root in $roots) { if ($full.StartsWith($root,[System.StringComparison]::OrdinalIgnoreCase)) { return Join-Path $script:RepoRoot ($full.Substring($root.Length).TrimStart('\')) } }
    $idx=$full.IndexOf('docs\chatgpt_status',[System.StringComparison]::OrdinalIgnoreCase); if ($idx -ge 0) { return Join-Path $script:RepoRoot $full.Substring($idx) }
    return $full
  }
  return Join-Path $script:RepoRoot $p
}
function Write-RepoFile([string]$RelPath,[object]$Payload) {
  $full=Join-Path $script:RepoRoot ($RelPath -replace '/', '\')
  $text = if ($Payload -is [string]) { $Payload } else { To-JsonText $Payload }
  Write-Utf8 $full $text
}
function Commit-And-Push([string]$Msg,[string[]]$Allowed) {
  $changed=Stage-Allowed $script:RepoRoot $Allowed
  $cached=Invoke-Git $script:RepoRoot diff --cached --name-only
  Git-Ok $cached "DIFF_CACHED_FAILED"
  if ($cached.output) { Git-Ok (Invoke-Git $script:RepoRoot commit -m $Msg) "COMMIT_FAILED" }
  if ($NoPush) { Add-Blocker "NO_PUSH_MODE"; return }
  Git-Ok (Invoke-Git $script:RepoRoot fetch origin $script:RunnerBranch) "POST_FETCH_FAILED"
  $rb=Invoke-Git $script:RepoRoot rebase ("origin/" + $script:RunnerBranch)
  if ($rb.code -ne 0) { throw ("BLOCKED_REBASE_CONFLICT: " + $rb.output) }
  Git-Ok (Invoke-Git $script:RepoRoot push origin ("HEAD:" + $script:RunnerBranch)) "POST_PUSH_FAILED"
}
function Commit-Runtime-Summary([string]$Msg) {
  $runtimeAllowed=@("docs/chatgpt_status/_shared/status","docs/chatgpt_status/_shared/heartbeat","docs/chatgpt_status/_shared/logs","docs/chatgpt_status/_shared/reports","docs/chatgpt_status/_shared/runner_lock")
  $runtimeDirty=@(Dirty-Paths $script:RepoRoot | Where-Object { Is-Runtime $_ })
  if ($runtimeDirty.Count -gt 0) { Commit-And-Push $Msg $runtimeAllowed }
}
function Run-Task([object]$Task) {
  $page=$Task.page_key; $taskId=$Task.task_id; $allowed=@($Task.allowed_paths)
  $script:Summary.queue_started=$true; $script:Summary.task_runs_in_clean_worktree=$script:InitialClean
  $started="docs/chatgpt_status/$page/status/${taskId}_started.json"
  $heartbeat="docs/chatgpt_status/$page/heartbeat/${taskId}_heartbeat.txt"
  $report="docs/chatgpt_status/$page/runner_outputs/${taskId}.report.json"
  $completed="docs/chatgpt_status/$page/completed/${taskId}.completed.json"
  $blocked="docs/chatgpt_status/$page/blocked/${taskId}.blocked.json"
  $mirror="docs/chatgpt_status/_shared/status/queue_result_mirror_${taskId}.json"
  Write-RepoFile $started ([ordered]@{task_id=$taskId;page_key=$page;started_at=Now-Utc;queue_seen=$true;queue_started=$true;single_runner_lock_acquired=$true;task_runs_in_clean_worktree=$script:InitialClean;target_branch=$script:RunnerBranch;final_ready=$false;fake_data=$false;db_write=$false;migration=$false;production_deploy=$false})
  Write-RepoFile $heartbeat "TASK_ID=$taskId`nPAGE_KEY=$page`nSTATUS=running`nHEARTBEAT_AT=$(Now-Utc)`n"
  Write-RepoFile $Task.queue_rel ([ordered]@{task_id=$taskId;page_key=$page;status="running";target_branch=$script:RunnerBranch;script_path=$Task.script_path;allowed_paths=$Task.allowed_paths;no_fake_final_ready=$true;no_db_write=$true;no_migration=$true;no_production_deploy=$true})
  $scriptPath=Resolve-Script $Task.script_path
  if (-not (Test-Path -LiteralPath $scriptPath)) { throw "SCRIPT_MISSING: $scriptPath" }
  Git-Ok (Invoke-Git $script:RepoRoot ls-remote origin) "BLOCKED_GITHUB_AUTH"
  if (-not $NoPush) { Git-Ok (Invoke-Git $script:RepoRoot push --dry-run origin ("HEAD:" + $script:RunnerBranch)) "BLOCKED_GITHUB_AUTH" }
  $oldRoot=$env:AAYS_REPO_ROOT; $oldTask=$env:AAYS_TASK_ID; $oldPage=$env:AAYS_PAGE_KEY; $oldBranch=$env:AAYS_TARGET_BRANCH
  $env:AAYS_REPO_ROOT=$script:RepoRoot; $env:AAYS_TASK_ID=$taskId; $env:AAYS_PAGE_KEY=$page; $env:AAYS_TARGET_BRANCH=$script:RunnerBranch
  $outText=""; $code=0
  try { Push-Location -LiteralPath $script:RepoRoot; try { $out=& powershell -NoProfile -ExecutionPolicy Bypass -File $scriptPath 2>&1; $code=$LASTEXITCODE; $outText=($out | Out-String) } finally { Pop-Location } } finally { $env:AAYS_REPO_ROOT=$oldRoot; $env:AAYS_TASK_ID=$oldTask; $env:AAYS_PAGE_KEY=$oldPage; $env:AAYS_TARGET_BRANCH=$oldBranch }
  if ($code -ne 0) { Add-Blocker "AUTOMATION_EXIT_NONZERO" }
  $tail=$outText; if ($tail.Length -gt 12000) { $tail=$tail.Substring($tail.Length-12000) }
  Write-RepoFile $report ([ordered]@{task_id=$taskId;page_key=$page;runner="RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_V5_20260706";updated_at=Now-Utc;target_branch=$script:RunnerBranch;queue_seen=$true;queue_started=$true;single_runner_lock_acquired=$true;task_runs_in_clean_worktree=$script:InitialClean;allowed_paths_enforced=$false;runner_output_uploaded=$true;post_sync_ok=$false;PUSH_SYNC_OK=$false;CONTINUE_RUNNER_READY=$true;automation_exit_code=$code;final_ready=$false;fake_data=$false;db_write=$false;ddl=$false;migration=$false;production_deploy=$false;blockers=@($script:Summary.blockers);automation_output_tail=$tail})
  $script:Summary.allowed_paths_enforced=$true
  Commit-And-Push "AAYS shared runner V5 output $page $taskId" $allowed
  if ($script:Summary.blockers.Count -eq 0 -and $code -eq 0) {
    $done=[ordered]@{task_id=$taskId;page_key=$page;completed_at=Now-Utc;status="completed";queue_seen=$true;queue_started=$true;single_runner_lock_acquired=$true;task_runs_in_clean_worktree=$script:InitialClean;allowed_paths_enforced=$true;runner_output_uploaded=$true;post_sync_ok=(-not $NoPush);PUSH_SYNC_OK=(-not $NoPush);CONTINUE_RUNNER_READY=$true;final_ready=$false;fake_data=$false;db_write=$false;ddl=$false;migration=$false;production_deploy=$false;blockers=@()}
    Write-RepoFile $completed $done; Write-RepoFile $mirror $done; Write-RepoFile $Task.queue_rel ([ordered]@{task_id=$taskId;page_key=$page;status="done";runner_completed_at=Now-Utc;PUSH_SYNC_OK=(-not $NoPush);CONTINUE_RUNNER_READY=$true;final_ready=$false;no_fake_final_ready=$true;no_db_write=$true;no_migration=$true;no_production_deploy=$true})
    Write-RepoFile $heartbeat "TASK_ID=$taskId`nPAGE_KEY=$page`nSTATUS=completed`nPUSH_SYNC_OK=$((-not $NoPush).ToString().ToLower())`nCONTINUE_RUNNER_READY=true`nFINAL_READY=false`nHEARTBEAT_AT=$(Now-Utc)`n"
  } else {
    $b=[ordered]@{task_id=$taskId;page_key=$page;blocked_at=Now-Utc;status="blocked";final_ready=$false;blockers=@($script:Summary.blockers);automation_exit_code=$code;fake_data=$false;db_write=$false;ddl=$false;migration=$false;production_deploy=$false}
    Write-RepoFile $blocked $b; Write-RepoFile $Task.queue_rel ([ordered]@{task_id=$taskId;page_key=$page;status="blocked";blocked_at=Now-Utc;blockers=@($script:Summary.blockers);final_ready=$false;no_fake_final_ready=$true;no_db_write=$true;no_migration=$true;no_production_deploy=$true})
    Write-RepoFile $heartbeat "TASK_ID=$taskId`nPAGE_KEY=$page`nSTATUS=blocked`nFINAL_READY=false`nHEARTBEAT_AT=$(Now-Utc)`n"
  }
  Commit-And-Push "AAYS shared runner V5 completion $page $taskId" $allowed
  $script:Summary.runner_output_uploaded=$true; $script:Summary.post_sync_ok=(-not $NoPush); $script:Summary.PUSH_SYNC_OK=(-not $NoPush); $script:Summary.CONTINUE_RUNNER_READY=$true
  return [pscustomobject]@{task_id=$taskId;page_key=$page;completed=($script:Summary.blockers.Count -eq 0 -and $code -eq 0);final_ready=$false}
}

$script:RepoRoot=[System.IO.Path]::GetFullPath((Get-RepoRoot))
$script:RunnerBranch = if ([string]::IsNullOrWhiteSpace($MainBranch)) { Get-Branch $script:RepoRoot } else { $MainBranch }
$script:WorkRoot=[System.IO.Path]::GetFullPath($WorkRoot)
$SharedRoot=Join-Path $script:RepoRoot "docs\chatgpt_status\_shared"
$StatusDir=Join-Path $SharedRoot "status"; $ReportDir=Join-Path $SharedRoot "reports"; $HeartbeatDir=Join-Path $SharedRoot "heartbeat"; $LockDir=Join-Path $SharedRoot "runner_lock"; $LogDir=Join-Path $SharedRoot "logs"
foreach ($d in @($StatusDir,$ReportDir,$HeartbeatDir,$LockDir,$LogDir)) { Ensure-Dir $d }
$RunId=Get-Date -Format "yyyyMMdd_HHmmss"
$script:GitLogPath=Join-Path $LogDir "MULTI_PAGE_git_args_V5_$RunId.log"
$LockPath=Join-Path $LockDir "MULTI_PAGE.lock"
$LatestStatusPath=Join-Path $StatusDir "MULTI_PAGE_latest_status.json"
$RunnerHeartbeatPath=Join-Path $HeartbeatDir "MULTI_PAGE_heartbeat_latest.json"
$script:Summary=[ordered]@{run_id=$RunId;checked_at=Now-Utc;repo_root=$script:RepoRoot;runner_branch=$script:RunnerBranch;queue_seen=$false;queue_started=$false;single_runner_lock_acquired=$false;task_runs_in_clean_worktree=$false;allowed_paths_enforced=$false;runner_output_uploaded=$false;post_sync_ok=$false;PUSH_SYNC_OK=$false;CONTINUE_RUNNER_READY=$false;final_ready=$false;fake_data=$false;db_write=$false;ddl=$false;migration=$false;production_deploy=$false;blockers=@();processed=@();skipped=@()}
try {
  Git-Ok (Invoke-Git $script:RepoRoot config core.longpaths true) "CONFIG_LONGPATHS_FAILED"
  $dirty=@(Dirty-Paths $script:RepoRoot); $realDirty=@($dirty | Where-Object { -not (Is-Runtime $_) })
  $script:InitialClean=($realDirty.Count -eq 0)
  if (-not $script:InitialClean) { throw ("CONTROLLER_DIRTY_NO_RUN: " + ($realDirty -join ',')) }
  Git-Ok (Invoke-Git $script:RepoRoot fetch origin $script:RunnerBranch) "CONTROLLER_FETCH_FAILED"
  Git-Ok (Invoke-Git $script:RepoRoot checkout $script:RunnerBranch) "CONTROLLER_CHECKOUT_FAILED"
  $pull=Invoke-Git $script:RepoRoot pull --ff-only origin $script:RunnerBranch; if ($pull.code -ne 0) { throw ("CONTROLLER_PULL_FAILED: " + $pull.output) }
  if (Test-Path -LiteralPath $LockPath) { $age=((Get-Date)-(Get-Item -LiteralPath $LockPath).LastWriteTime).TotalMinutes; if ($age -lt $StaleMinutes) { Add-Blocker "RUNNER_ALREADY_ACTIVE"; throw "RUNNER_ALREADY_ACTIVE" } else { Remove-Item -LiteralPath $LockPath -Force -Recurse -ErrorAction SilentlyContinue } }
  Ensure-Dir $LockPath; $script:Summary.single_runner_lock_acquired=$true
  Write-Utf8 $RunnerHeartbeatPath (To-JsonText ([ordered]@{pid=$PID;started_at=Now-Utc;runner="RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_V5_20260706";runner_branch=$script:RunnerBranch;repo_root=$script:RepoRoot}))
  $queueFiles=@(Get-ChildItem -LiteralPath (Join-Path $script:RepoRoot "docs\chatgpt_status") -Recurse -File -ErrorAction SilentlyContinue | Where-Object { $_.FullName -match '\\queue\\' })
  $parsed=@($queueFiles | ForEach-Object { Parse-Queue $_ })
  $ready=@($parsed | Where-Object { $_.valid -and $_.status_norm -in $RunnableStatuses } | Sort-Object priority,page_key,task_id)
  $script:Summary.queue_seen=($parsed.Count -gt 0)
  Write-Utf8 (Join-Path $StatusDir "queue_selection_debug_20260706_v5.json") (To-JsonText ([ordered]@{checked_at=Now-Utc;ready_count=$ready.Count;ready=$ready}))
  Write-Utf8 (Join-Path $StatusDir "queue_skip_status_check_20260706_v5.json") (To-JsonText ([ordered]@{checked_at=Now-Utc;skipped=@($parsed | Where-Object { -not $_.valid -or -not ($_.status_norm -in $RunnableStatuses) })}))
  if (-not $ScanOnly) { $count=0; foreach ($task in $ready) { if ($count -ge $MaxTasksPerScan) { break }; $res=Run-Task $task; $script:Summary.processed += $res; $count++ } }
  $script:Summary.CONTINUE_RUNNER_READY=$true
} catch { Add-Blocker ("RUNNER_FATAL: " + $_.Exception.Message) } finally {
  try { Write-Utf8 $LatestStatusPath (To-JsonText $script:Summary) } catch {}
  try { Write-Utf8 (Join-Path $ReportDir "MULTI_PAGE_runner_output_V5_$RunId.json") (To-JsonText $script:Summary) } catch {}
  try { if (Test-Path -LiteralPath $LockPath) { Remove-Item -LiteralPath $LockPath -Force -Recurse -ErrorAction SilentlyContinue } } catch {}
}
try {
  Commit-Runtime-Summary "AAYS shared runner V5 scan summary $RunId"
} catch {
  Add-Blocker ("SUMMARY_PUSH_FAILED: " + $_.Exception.Message)
  try { Write-Utf8 $LatestStatusPath (To-JsonText $script:Summary) } catch {}
}
Write-Output (To-JsonText $script:Summary)
if ($script:Summary.blockers.Count -gt 0) { exit 1 }
exit 0
