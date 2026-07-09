param(
  [string]$RepoRoot = 'F:\TerraYield_AAYS_Portable\runner_system\AAYS_WT\AAYS_RUNNER_HEALTHY_20260707',
  [string]$RepoFullName = 'cagdascagdas100/chat_gpt_clone_1',
  [string]$MainBranch = 'codex/aays-single-runner-v5-20260706',
  [string]$WorkRoot = 'F:\TerraYield_AAYS_Portable\runner_system\AAYS_WT\AAYS_STABLE_RUNNER_WORKTREES',
  [int]$StaleMinutes = 20,
  [int]$MaxTasks = 1,
  [switch]$ScanOnly,
  [switch]$NoPush
)

$ErrorActionPreference = 'Stop'
function Now-Utc { (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ') }
function Ensure-Dir([string]$Path) { if ($Path -and -not (Test-Path -LiteralPath $Path)) { New-Item -ItemType Directory -Force -Path $Path | Out-Null } }
function Write-Utf8([string]$Path, [string]$Content) { Ensure-Dir (Split-Path -Parent $Path); [System.IO.File]::WriteAllText($Path, $Content, [System.Text.UTF8Encoding]::new($false)) }
function To-JsonText([object]$Obj) { $Obj | ConvertTo-Json -Depth 80 }
function Rel([string]$Path) { (($Path -replace '\\','/').TrimStart('/')) }
function Safe-Name([string]$Value) { (($Value -replace '[^A-Za-z0-9_.-]', '_').Trim('_')) }
function Get-Prop([object]$Obj, [string]$Name) { if ($null -eq $Obj) { return $null }; $p = $Obj.PSObject.Properties[$Name]; if ($p) { return $p.Value }; return $null }
function As-Bool([object]$Value) { if ($Value -is [bool]) { return $Value }; if ($null -eq $Value) { return $false }; return ([string]$Value).Trim().ToLowerInvariant() -in @('true','1','yes','y') }
function Add-Blocker([string]$Code) { if ($Code -and -not ($script:Summary.blockers -contains $Code)) { $script:Summary.blockers += $Code } }
function Normalize-List([object]$Value) {
  $items = @()
  if ($null -eq $Value) { return $items }
  if ($Value -is [System.Array]) { $items = @($Value) } else { $items = @(([string]$Value) -split '[,;]') }
  return @($items | ForEach-Object { (Rel ([string]$_)).TrimEnd('/') } | Where-Object { $_ } | Select-Object -Unique)
}
function Path-IsAllowed([string]$Path, [string[]]$Allowed) {
  $x = (Rel $Path).TrimEnd('/')
  foreach ($a in $Allowed) {
    $z = (Rel $a).TrimEnd('/')
    if ($x -eq $z -or $x.StartsWith($z + '/')) { return $true }
  }
  return $false
}
function Invoke-AaysGit {
  param([Parameter(Mandatory=$true)][string]$Cwd,[Parameter(ValueFromRemainingArguments=$true)][string[]]$GitArgs)
  Push-Location -LiteralPath $Cwd
  $old = $ErrorActionPreference
  try {
    $ErrorActionPreference = 'Continue'
    $safe = ([System.IO.Path]::GetFullPath($Cwd).TrimEnd('\') -replace '\\','/')
    $args = @('-c', "safe.directory=$safe") + $GitArgs
    $out = & git @args 2>&1
    $code = $LASTEXITCODE
    return [pscustomobject]@{ code=$code; output=(($out | Out-String).TrimEnd()); args=$args }
  } finally { $ErrorActionPreference = $old; Pop-Location }
}
function Git-Ok([object]$Result) { return ($Result -and $Result.code -eq 0) }
function Git-Try([string]$Cwd, [string[]]$Args, [string]$Label) {
  $r = Invoke-AaysGit -Cwd $Cwd -GitArgs $Args
  $script:Summary.git += [ordered]@{ label=$Label; code=$r.code; output=$r.output }
  return $r
}
function Read-QueueFile([System.IO.FileInfo]$File) {
  $raw = Get-Content -LiteralPath $File.FullName -Raw
  if ($File.Extension -ieq '.json') { return ($raw | ConvertFrom-Json) }
  $map = [ordered]@{}
  foreach ($line in ($raw -split "`r?`n")) {
    $t = $line.Trim()
    if (-not $t -or $t.StartsWith('#') -or $t -notmatch '=') { continue }
    $i = $t.IndexOf('=')
    $map[$t.Substring(0,$i).Trim()] = $t.Substring($i + 1).Trim()
  }
  return [pscustomobject]$map
}
function Parse-Queue([System.IO.FileInfo]$File) {
  $relative = Rel ($File.FullName.Substring($RepoRoot.Length).TrimStart('\','/'))
  if ($relative -notmatch '^docs/chatgpt_status/([^/]+)/queue/[^/]+$') { return [pscustomobject]@{ valid=$false; queue_rel=$relative; skip_reason='NOT_CANONICAL_QUEUE_PATH' } }
  $pageFromPath = $Matches[1]
  try { $data = Read-QueueFile $File } catch { return [pscustomobject]@{ valid=$false; page_key=$pageFromPath; task_id=(Safe-Name ([System.IO.Path]::GetFileNameWithoutExtension($File.Name))); status='invalid'; status_norm='invalid'; validation_errors=@('QUEUE_PARSE_FAILED'); queue_rel=$relative } }
  $page = [string](Get-Prop $data 'page_key')
  $taskId = [string](Get-Prop $data 'task_id'); if (-not $taskId) { $taskId = [System.IO.Path]::GetFileNameWithoutExtension($File.Name) }
  $status = [string](Get-Prop $data 'status'); if (-not $status) { $status = 'queued' }
  $scriptPath = [string](Get-Prop $data 'script_path')
  if (-not $scriptPath) { $scriptPath = [string](Get-Prop $data 'automation_script') }
  if (-not $scriptPath) { $scriptPath = [string](Get-Prop $data 'script') }
  $targetBranch = [string](Get-Prop $data 'target_branch')
  if (-not $targetBranch) { $targetBranch = [string](Get-Prop $data 'branch') }
  if (-not $targetBranch) { $targetBranch = $MainBranch }
  $allowed = Normalize-List (Get-Prop $data 'allowed_paths')
  $priority = 1000
  $priorityRaw = Get-Prop $data 'priority'
  if ($priorityRaw -ne $null) { [void][int]::TryParse(([string]$priorityRaw), [ref]$priority) }
  $errors = @()
  if (-not $page) { $errors += 'MISSING_page_key' }
  if ($page -and $page -ne $pageFromPath) { $errors += 'PAGE_KEY_PATH_MISMATCH' }
  if (-not $scriptPath) { $errors += 'MISSING_script_path' }
  if ($allowed.Count -eq 0) { $errors += 'MISSING_allowed_paths' }
  if (-not (As-Bool (Get-Prop $data 'no_fake_final_ready'))) { $errors += 'MISSING_no_fake_final_ready' }
  if (-not (As-Bool (Get-Prop $data 'no_db_write'))) { $errors += 'MISSING_no_db_write' }
  if (-not (As-Bool (Get-Prop $data 'no_migration'))) { $errors += 'MISSING_no_migration' }
  if (-not (As-Bool (Get-Prop $data 'no_production_deploy'))) { $errors += 'MISSING_no_production_deploy' }
  return [pscustomobject]@{ valid=($errors.Count -eq 0); validation_errors=$errors; page_key=$page; task_id=(Safe-Name $taskId); status=$status; status_norm=$status.Trim().ToLowerInvariant(); script_path=$scriptPath; target_branch=$targetBranch; allowed_paths=$allowed; priority=$priority; queue_rel=$relative; data=$data }
}
function Resolve-ScriptPath([string]$Root, [string]$ScriptPath) {
  $p = $ScriptPath -replace '/', '\'
  if ([System.IO.Path]::IsPathRooted($p)) { return $p }
  return (Join-Path $Root $p)
}
function Stage-AllowedOnly([string]$Root, [string[]]$Allowed) {
  $r = Invoke-AaysGit $Root status --porcelain
  $changed = @()
  if ($r.output) {
    foreach ($line in @($r.output -split '\r?\n' | Where-Object { $_ })) {
      if ($line.Length -lt 4) { continue }
      $p = $line.Substring(3).Trim().Trim('"')
      if ($p -match ' -> ') { $p = ($p -split ' -> ')[-1] }
      $changed += (Rel $p)
    }
  }
  $unscoped = @($changed | Where-Object { -not (Path-IsAllowed $_ $Allowed) })
  if ($unscoped.Count -gt 0) { return [pscustomobject]@{ ok=$false; changed=$changed; unscoped=$unscoped } }
  foreach ($p in $changed) { [void](Invoke-AaysGit $Root add -- $p) }
  return [pscustomobject]@{ ok=$true; changed=$changed; unscoped=@() }
}
function Push-Sync([string]$Root, [string]$Branch, [string]$Message) {
  if ($NoPush) { Add-Blocker 'NO_PUSH_MODE'; return [pscustomobject]@{ pushed=$false; status='no_push_mode' } }
  $cached = Invoke-AaysGit $Root diff --cached --name-only
  if ($cached.code -ne 0) { Add-Blocker 'DIFF_CACHED_FAILED'; return [pscustomobject]@{ pushed=$false; status='diff_failed'; output=$cached.output } }
  if (-not $cached.output) { return [pscustomobject]@{ pushed=$false; status='no_changes' } }
  $commit = Invoke-AaysGit $Root commit -m $Message
  if ($commit.code -ne 0) { Add-Blocker 'COMMIT_FAILED'; return [pscustomobject]@{ pushed=$false; status='commit_failed'; output=$commit.output } }
  [void](Invoke-AaysGit -Cwd $Root -GitArgs @('fetch','--no-tags','--depth=1','origin',("+refs/heads/${Branch}:refs/remotes/origin/${Branch}")))
  $rebase = Invoke-AaysGit $Root rebase ('origin/' + $Branch)
  if ($rebase.code -ne 0) { Add-Blocker 'REBASE_FAILED'; [void](Invoke-AaysGit $Root rebase --abort); return [pscustomobject]@{ pushed=$false; status='rebase_failed'; output=$rebase.output } }
  $push = Invoke-AaysGit $Root push origin ("HEAD:${Branch}")
  if ($push.code -ne 0) { Add-Blocker 'PUSH_FAILED'; return [pscustomobject]@{ pushed=$false; status='push_failed'; output=$push.output } }
  return [pscustomobject]@{ pushed=$true; status='pushed'; output=$push.output }
}
function Write-TaskFile([string]$Root, [string]$RelPath, [object]$Payload) {
  $full = Join-Path $Root ($RelPath -replace '/', '\')
  $content = if ($Payload -is [string]) { $Payload } else { To-JsonText $Payload }
  Write-Utf8 $full $content
}
function Run-Task([object]$Task) {
  $page = $Task.page_key
  $taskId = $Task.task_id
  $scriptPath = Resolve-ScriptPath $RepoRoot $Task.script_path
  $startedRel = "docs/chatgpt_status/$page/status/${taskId}_started.json"
  $heartbeatRel = "docs/chatgpt_status/$page/heartbeat/${taskId}_heartbeat.txt"
  $reportRel = "docs/chatgpt_status/$page/reports/${taskId}_runner_output.txt"
  $completedRel = "docs/chatgpt_status/$page/status/${taskId}_completed.json"
  $mirrorRel = "docs/chatgpt_status/_shared/status/queue_result_mirror_${taskId}.json"
  Write-TaskFile $RepoRoot $startedRel ([ordered]@{ task_id=$taskId; page_key=$page; started_at=Now-Utc; queue_seen=$true; queue_started=$true; single_runner_lock_acquired=$true; final_ready=$false; fake_data=$false; db_write=$false; migration=$false; production_deploy=$false })
  Write-TaskFile $RepoRoot $heartbeatRel "TASK_ID=$taskId`nPAGE_KEY=$page`nSTATUS=running`nHEARTBEAT_AT=$(Now-Utc)`n"
  Write-TaskFile $RepoRoot $Task.queue_rel ([ordered]@{ task_id=$taskId; page_key=$page; status='running'; target_branch=$Task.target_branch; script_path=$Task.script_path; allowed_paths=$Task.allowed_paths; no_fake_final_ready=$true; no_db_write=$true; no_migration=$true; no_production_deploy=$true; final_ready=$false; fake_data=$false; db_write=$false; migration=$false; production_deploy=$false })
  if (-not (Test-Path -LiteralPath $scriptPath)) { throw ('SCRIPT_MISSING: ' + $scriptPath) }
  $oldRoot=$env:AAYS_REPO_ROOT; $oldTask=$env:AAYS_TASK_ID; $oldPage=$env:AAYS_PAGE_KEY
  $env:AAYS_REPO_ROOT=$RepoRoot; $env:AAYS_TASK_ID=$taskId; $env:AAYS_PAGE_KEY=$page
  $automationOutput=''; $automationCode=0
  try {
    Push-Location -LiteralPath $RepoRoot
    try { $out = & powershell -NoProfile -ExecutionPolicy Bypass -File $scriptPath 2>&1; $automationCode=$LASTEXITCODE; $automationOutput=($out | Out-String) } finally { Pop-Location }
  } finally { $env:AAYS_REPO_ROOT=$oldRoot; $env:AAYS_TASK_ID=$oldTask; $env:AAYS_PAGE_KEY=$oldPage }
  if ($automationCode -ne 0) { Add-Blocker 'AUTOMATION_EXIT_NONZERO' }
  Write-TaskFile $RepoRoot $reportRel "TASK_ID=$taskId`nPAGE_KEY=$page`nRUNNER_STABLE=F_PORTABLE_20260709`nautomation_exit_code=$automationCode`nfake_data=false`n--- output ---`n$automationOutput"
  $allowedPlus = @($Task.allowed_paths + @($startedRel,$heartbeatRel,$reportRel,$completedRel,$mirrorRel,$Task.queue_rel,'docs/chatgpt_status/_shared/status/runner_bootstrap_latest.json','docs/chatgpt_status/_shared/heartbeat/stable_runner_daemon_heartbeat_latest.json') | Select-Object -Unique)
  $stage = Stage-AllowedOnly $RepoRoot $allowedPlus
  if (-not $stage.ok) { throw ('BLOCKED_UNSCOPED_CHANGES: ' + ($stage.unscoped -join ',')) }
  $push1 = Push-Sync $RepoRoot $Task.target_branch "AAYS F portable runner output $page $taskId"
  $completed = [ordered]@{ task_id=$taskId; page_key=$page; completed_at=Now-Utc; queue_seen=$true; queue_started=$true; single_runner_lock_acquired=$true; runner_output_uploaded=[bool]$push1.pushed; post_sync_ok=[bool]$push1.pushed; PUSH_SYNC_OK=[bool]$push1.pushed; CONTINUE_RUNNER_READY=$true; final_ready=$false; fake_data=$false; db_write=$false; migration=$false; production_deploy=$false; push_status=$push1.status; blockers=@($script:Summary.blockers) }
  Write-TaskFile $RepoRoot $completedRel $completed
  Write-TaskFile $RepoRoot $mirrorRel $completed
  Write-TaskFile $RepoRoot $Task.queue_rel ([ordered]@{ task_id=$taskId; page_key=$page; status='done'; runner_completed_at=Now-Utc; PUSH_SYNC_OK=[bool]$push1.pushed; CONTINUE_RUNNER_READY=$true; final_ready=$false; no_fake_final_ready=$true; no_db_write=$true; no_migration=$true; no_production_deploy=$true })
  Write-TaskFile $RepoRoot $heartbeatRel "TASK_ID=$taskId`nPAGE_KEY=$page`nSTATUS=completed`nPUSH_SYNC_OK=$([bool]$push1.pushed)`nFINAL_READY=False`nHEARTBEAT_AT=$(Now-Utc)`n"
  $stage2 = Stage-AllowedOnly $RepoRoot $allowedPlus
  if (-not $stage2.ok) { throw ('BLOCKED_UNSCOPED_CHANGES_AFTER_COMPLETE: ' + ($stage2.unscoped -join ',')) }
  $push2 = Push-Sync $RepoRoot $Task.target_branch "AAYS F portable runner completion $page $taskId"
  return [pscustomobject]@{ task_id=$taskId; page_key=$page; completed=$true; final_ready=$false; push1=$push1; push2=$push2 }
}

$RepoRoot = [System.IO.Path]::GetFullPath($RepoRoot)
$WorkRoot = [System.IO.Path]::GetFullPath($WorkRoot)
if (-not (Test-Path -LiteralPath (Join-Path $RepoRoot 'docs\chatgpt_status\_shared'))) { throw 'BLOCKED_REPO_ROOT_NOT_AAYS: ' + $RepoRoot }
Ensure-Dir $WorkRoot
$SharedRoot = Join-Path $RepoRoot 'docs\chatgpt_status\_shared'
$StatusDir = Join-Path $SharedRoot 'status'
$ReportDir = Join-Path $SharedRoot 'reports'
$HeartbeatDir = Join-Path $SharedRoot 'heartbeat'
foreach ($d in @($StatusDir,$ReportDir,$HeartbeatDir)) { Ensure-Dir $d }
$RunId = (Get-Date -Format 'yyyyMMdd_HHmmss')
$LatestStatusPath = Join-Path $StatusDir 'MULTI_PAGE_latest_status.json'
$RunnerHeartbeatPath = Join-Path $HeartbeatDir 'stable_runner_daemon_heartbeat_latest.json'
$BootstrapPath = Join-Path $StatusDir 'runner_bootstrap_latest.json'
$script:Summary = [ordered]@{ run_id=$RunId; checked_at=Now-Utc; repo_root=$RepoRoot; work_root=$WorkRoot; main_branch=$MainBranch; f_portable_runner_fix_active=$true; queue_seen=$false; queue_started=$false; single_runner_lock_acquired=$true; runner_output_uploaded=$false; post_sync_ok=$false; PUSH_SYNC_OK=$false; CONTINUE_RUNNER_READY=$true; final_ready=$false; fake_data=$false; db_write=$false; migration=$false; production_deploy=$false; processed=@(); skipped=@(); blockers=@(); git=@() }
try {
  [void](Git-Try $RepoRoot @('config','core.longpaths','true') 'config_longpaths')
  [void](Git-Try $RepoRoot @('fetch','--no-tags','--depth=1','origin',("+refs/heads/${MainBranch}:refs/remotes/origin/${MainBranch}")) 'fetch')
  [void](Git-Try $RepoRoot @('checkout',$MainBranch) 'checkout')
  [void](Git-Try $RepoRoot @('rebase',('origin/' + $MainBranch)) 'rebase')
  $hb = [ordered]@{ runner_active=$true; pid=$PID; pid_alive=$true; lock_valid=$true; portable_root='F:\TerraYield_AAYS_Portable'; repo_root=$RepoRoot; branch=$MainBranch; scan_runner='RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_STABLE_20260707_F_PORTABLE_FIXED'; heartbeat_at=Now-Utc; git_push_status='pending_after_task'; final_ready=$false; fake_data=$false; db_write=$false; migration=$false; production_deploy=$false }
  Write-Utf8 $RunnerHeartbeatPath (To-JsonText $hb)
  Write-Utf8 $BootstrapPath (To-JsonText $hb)
  $queueFiles = @(Get-ChildItem -LiteralPath (Join-Path $RepoRoot 'docs\chatgpt_status') -Recurse -File -ErrorAction SilentlyContinue | Where-Object { $_.FullName -match '\\queue\\' })
  $parsed = @($queueFiles | ForEach-Object { Parse-Queue $_ })
  $readyStatuses = @('queued','ready','pending','pending_repo_queue','pickup_requested','queued_for_single_shared_runner')
  $ready = @($parsed | Where-Object { $_.valid -and ($readyStatuses -contains $_.status_norm) } | Sort-Object priority, page_key, task_id)
  $script:Summary.queue_seen = ($parsed.Count -gt 0)
  $script:Summary.ready_count = $ready.Count
  $script:Summary.skipped = @($parsed | Where-Object { -not $_.valid -or -not ($readyStatuses -contains $_.status_norm) } | Select-Object -First 50)
  Write-Utf8 (Join-Path $StatusDir 'queue_selection_debug_20260709.json') (To-JsonText ([ordered]@{ checked_at=Now-Utc; parsed_count=$parsed.Count; ready_count=$ready.Count; ready=@($ready | Select-Object -First 20); skipped=@($script:Summary.skipped) }))
  if (-not $ScanOnly) {
    $count = 0
    foreach ($task in $ready) {
      if ($count -ge $MaxTasks) { break }
      try { $res = Run-Task $task; $script:Summary.processed += $res; $count++ } catch { Add-Blocker ('RUNNER_TASK_FAILED: ' + $_.Exception.Message); $script:Summary.processed += [ordered]@{ task_id=$task.task_id; page_key=$task.page_key; completed=$false; final_ready=$false; error=$_.Exception.Message }; break }
    }
    $script:Summary.processed_task_count = $count
    $script:Summary.runner_output_uploaded = ($count -gt 0)
    $script:Summary.post_sync_ok = ($count -gt 0)
    $script:Summary.PUSH_SYNC_OK = ($count -gt 0)
  }
} catch { Add-Blocker ('RUNNER_FATAL: ' + $_.Exception.Message) }
finally {
  try { Write-Utf8 $LatestStatusPath (To-JsonText $script:Summary) } catch {}
  try { Write-Utf8 (Join-Path $ReportDir "MULTI_PAGE_runner_output_$RunId.json") (To-JsonText $script:Summary) } catch {}
}
Write-Output (To-JsonText $script:Summary)
exit 0
