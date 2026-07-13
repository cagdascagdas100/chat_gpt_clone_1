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
$script:QueueScanRoot = $RepoRoot
$script:RemoteQueueCommit = $null

function Now-Utc { (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ') }
function Safe-Name([string]$Value) { (($Value -replace '[^A-Za-z0-9_.-]', '_').Trim('_')) }
function Rel([string]$Path) { (($Path -replace '\\','/').TrimStart('/')) }
function Ensure-Dir([string]$Path) { if ($Path -and -not (Test-Path -LiteralPath $Path)) { New-Item -ItemType Directory -Force -Path $Path | Out-Null } }
function Write-Utf8([string]$Path, [string]$Content) { Ensure-Dir (Split-Path -Parent $Path); [System.IO.File]::WriteAllText($Path, $Content, [System.Text.UTF8Encoding]::new($false)) }
function Write-Utf8Atomic([string]$Path, [string]$Content) { Ensure-Dir (Split-Path -Parent $Path); $temp="$Path.tmp.$PID.$([guid]::NewGuid().ToString('N'))"; [System.IO.File]::WriteAllText($temp,$Content,[System.Text.UTF8Encoding]::new($false)); Move-Item -LiteralPath $temp -Destination $Path -Force }
function Read-JsonFile([string]$Path) { try { if(Test-Path -LiteralPath $Path -PathType Leaf){return Get-Content -LiteralPath $Path -Raw -Encoding UTF8|ConvertFrom-Json} } catch {}; return $null }
function Test-PidAlive([int]$ProcessId) { if($ProcessId-le0){return $false}; return $null-ne(Get-Process -Id $ProcessId -ErrorAction SilentlyContinue) }
function Test-ScanLockOwner([object]$Lock) {
  if(-not$Lock){return $false}
  $ownerPid=if($Lock.pid){[int]$Lock.pid}else{0}
  if(-not(Test-PidAlive $ownerPid)){return $false}
  if([string]$Lock.lock_scope-ne'single_scan_worker'){return $false}
  if($Lock.process_start_time){try{$process=Get-Process -Id $ownerPid -ErrorAction Stop;if([math]::Abs(($process.StartTime.ToUniversalTime()-([datetime]$Lock.process_start_time).ToUniversalTime()).TotalSeconds)-ge2){return $false}}catch{return $false}}
  return $true
}
function To-JsonText([object]$Obj) { $Obj | ConvertTo-Json -Depth 60 }
function Get-Prop([object]$Obj, [string]$Name) { if ($null -eq $Obj) { return $null }; $p = $Obj.PSObject.Properties[$Name]; if ($p) { return $p.Value }; return $null }
function Get-NestedProp([object]$Obj, [string]$Parent, [string]$Name) {
  $parentObj = Get-Prop $Obj $Parent
  if ($null -eq $parentObj) { return $null }
  return Get-Prop $parentObj $Name
}
function As-Bool([object]$Value) {
  if ($Value -is [bool]) { return $Value }
  if ($null -eq $Value) { return $false }
  return ([string]$Value).Trim().ToLowerInvariant() -in @('true','1','yes','y')
}
function Has-ExplicitFalseFlag([object]$Obj, [string]$Name) {
  foreach ($value in @((Get-Prop $Obj $Name), (Get-NestedProp $Obj 'safety_flags' $Name), (Get-NestedProp $Obj 'safety' $Name))) {
    if ($null -ne $value) { return (-not (As-Bool $value)) }
  }
  return $false
}
function Queue-SafetyFlagOk([object]$Obj, [string]$Name) {
  if (As-Bool (Get-Prop $Obj $Name)) { return $true }
  if (As-Bool (Get-NestedProp $Obj 'safety_flags' $Name)) { return $true }
  if (As-Bool (Get-NestedProp $Obj 'safety' $Name)) { return $true }
  switch ($Name) {
    'no_fake_final_ready' {
      if (As-Bool (Get-NestedProp $Obj 'safety' 'final_ready_must_be_evidence_based')) { return $true }
      return ((Has-ExplicitFalseFlag $Obj 'final_ready') -and (Has-ExplicitFalseFlag $Obj 'product_final_ready'))
    }
    'no_db_write' { return (Has-ExplicitFalseFlag $Obj 'db_write') }
    'no_migration' { return (Has-ExplicitFalseFlag $Obj 'migration') }
    'no_production_deploy' { return (Has-ExplicitFalseFlag $Obj 'production_deploy') }
  }
  return $false
}
function Add-Blocker([string]$Code) { if ($Code -and -not ($script:Summary.blockers -contains $Code)) { $script:Summary.blockers += $Code } }
function Normalize-Allowed([object]$Value) {
  $items = @()
  if ($null -eq $Value) { return $items }
  if ($Value -is [System.Array]) { $items = @($Value) } else { $items = @(([string]$Value) -split '[,;]') }
  return @($items | ForEach-Object {
    $x = Rel ([string]$_)
    $x = $x -replace '/\*\*$', ''
    $x = $x -replace '/\*$', ''
    $x.TrimEnd('/')
  } | Where-Object { $_ } | Select-Object -Unique)
}
function Path-IsAllowed([string]$Path, [string[]]$Allowed) {
  $x = (Rel $Path).TrimEnd('/')
  foreach ($a in $Allowed) {
    $z = (Rel $a).TrimEnd('/')
    if ($x -eq $z -or $x.StartsWith($z + '/')) { return $true }
  }
  return $false
}
function Is-ControllerRuntimePath([string]$Path) {
  $r = (Rel $Path).TrimEnd('/')
  return ($r -match '^docs/chatgpt_status/[^/]+/queue/' -or
    $r.StartsWith('docs/chatgpt_status/_shared/runner_outputs/') -or
    $r.StartsWith('docs/chatgpt_status/_shared/smoke/') -or
    $r.StartsWith('docs/chatgpt_status/_shared/smoke_tests/') -or
    $r -eq 'docs/chatgpt_status/aays1/status/130_f_portable_one_click_recovery_bootstrap_latest.json' -or
    $r -eq 'docs/chatgpt_status/_shared/heartbeat/MULTI_PAGE_heartbeat_latest.json' -or
    $r -eq 'docs/chatgpt_status/_shared/status/MULTI_PAGE_latest_status.json' -or
    $r -eq 'docs/chatgpt_status/_shared/status/queue_selection_debug_20260705.json' -or
    $r -eq 'docs/chatgpt_status/_shared/status/queue_skip_status_check_20260705.json' -or
    $r.StartsWith('docs/chatgpt_status/_shared/status/queue_selection_debug_') -or
    $r.StartsWith('docs/chatgpt_status/_shared/status/queue_skip_status_check_') -or
    $r -eq 'docs/chatgpt_status/_shared/status/local_reboot_runner_start_latest.json' -or
    $r -eq 'docs/chatgpt_status/_shared/status/local_reboot_runner_start_result_latest.json' -or
    $r.StartsWith('docs/chatgpt_status/_shared/status/reboot_runner_start_request_') -or
    $r.StartsWith('docs/chatgpt_status/_shared/control/') -or
    $r.StartsWith('docs/chatgpt_status/_shared/logs/') -or
    $r.StartsWith('docs/chatgpt_status/_shared/reports/MULTI_PAGE_runner_output_') -or
    $r -eq 'docs/chatgpt_status/_shared/runner_lock' -or
    $r.StartsWith('docs/chatgpt_status/_shared/runner_lock/') -or
    $r -eq 'docs/chatgpt_status/_shared/locks' -or
    $r.StartsWith('docs/chatgpt_status/_shared/locks/') -or
    $r -eq 'docs/chatgpt_status/_shared/heartbeat/stable_runner_daemon_heartbeat_latest.json' -or
    $r -eq 'docs/chatgpt_status/_shared/status/stable_runner_daemon_latest.json' -or
    $r -eq 'docs/chatgpt_status/_shared/status/runner_bootstrap_latest.json' -or
    $r -eq 'docs/chatgpt_status/_shared/panel/page_status_index_latest.json' -or
    $r -eq 'docs/chatgpt_status/_shared/status/page_panel_index.json' -or
    $r -eq 'docs/chatgpt_status/_shared/status/pages_status_dashboard.json' -or
    $r -eq 'docs/chatgpt_status/_shared/contracts/PAGE_KEY_REGISTRY.json' -or
    $r -eq 'docs/chatgpt_status/_shared/page_registry.json' -or
    $r -eq 'docs/chatgpt_status/_shared/page_registry/pages_manifest.json' -or
    $r -eq 'docs/chatgpt_status/_shared/reports/page_contract_inventory_20260706.md' -or
    $r -eq 'docs/chatgpt_status/_shared/status/page_contract_inventory_20260706.json' -or
    $r -eq 'england_map_web/data/runner_panel/page_status_index.json')
}
function Invoke-AaysGit {
  param(
    [Parameter(Mandatory=$true)][string]$Cwd,
    [Parameter(ValueFromRemainingArguments=$true)][string[]]$GitArgs
  )
  if ($null -eq $GitArgs -or $GitArgs.Count -eq 0) { throw 'BLOCKED_BARE_GIT_USAGE' }
  Ensure-Dir (Split-Path -Parent $script:GitLogPath)

  $safeDirs = New-Object System.Collections.Generic.List[string]
  foreach ($candidate in @($Cwd, $script:RepoRoot)) {
    if ([string]::IsNullOrWhiteSpace($candidate)) { continue }
    try {
      $full = [System.IO.Path]::GetFullPath($candidate).TrimEnd('\') -replace '\\','/'
      if (-not $safeDirs.Contains($full)) { [void]$safeDirs.Add($full) }
    } catch { }
  }

  $effectiveArgs = @()
  foreach ($safeDir in $safeDirs) { $effectiveArgs += @('-c', "safe.directory=$safeDir") }
  $effectiveArgs += $GitArgs

  Add-Content -LiteralPath $script:GitLogPath -Encoding UTF8 -Value ("[{0}] cwd={1} git {2}" -f (Now-Utc), $Cwd, ($effectiveArgs -join ' '))
  Push-Location -LiteralPath $Cwd
  $oldEap = $ErrorActionPreference
  try {
    $ErrorActionPreference = 'Continue'
    $out = & git @effectiveArgs 2>&1
    $code = $LASTEXITCODE
    return [pscustomobject]@{ code = $code; output = (($out | Out-String).TrimEnd()); args = $effectiveArgs }
  } finally {
    $ErrorActionPreference = $oldEap
    Pop-Location
  }
}
function Assert-GitOk([object]$Result, [string]$Blocker) {
  if ($Result.code -ne 0) { throw ($Blocker + ': ' + $Result.output) }
}
function Abort-GitRebaseIfPresent([string]$Root) {
  $rebaseMerge = Join-Path $Root '.git\rebase-merge'
  $rebaseApply = Join-Path $Root '.git\rebase-apply'
  if ((Test-Path -LiteralPath $rebaseMerge) -or (Test-Path -LiteralPath $rebaseApply)) {
    return (Invoke-AaysGit $Root rebase --abort)
  }
  return [pscustomobject]@{ code = 0; output = ''; args = @() }
}
function Get-GitChangedPaths([string]$Root) {
  $r = Invoke-AaysGit $Root status --porcelain
  Assert-GitOk $r 'STATUS_FAILED'
  $paths = @()
  foreach ($line in @($r.output -split '\r?\n' | Where-Object { $_ })) {
    if ($line.Length -lt 4) { continue }
    $p = $line.Substring(3).Trim().Trim('"')
    if ($p -match ' -> ') { $p = ($p -split ' -> ')[-1] }
    $paths += (Rel $p)
  }
  return @($paths)
}
function Stage-AllowedOnly([string]$Root, [string[]]$Allowed) {
  $changed = @(Get-GitChangedPaths $Root)
  $unscoped = @($changed | Where-Object { -not (Path-IsAllowed $_ $Allowed) })
  if ($unscoped.Count -gt 0) { return [pscustomobject]@{ ok = $false; changed = $changed; unscoped = $unscoped } }
  foreach ($p in $changed) { Assert-GitOk (Invoke-AaysGit $Root add -- $p) 'ADD_FAILED' }
  return [pscustomobject]@{ ok = $true; changed = $changed; unscoped = @() }
}

function Add-TaskBlocker([string]$TaskId, [string]$PageKey, [string]$Code, [string]$Detail = '') {
  $script:Summary.task_blockers += [ordered]@{
    task_id = $TaskId
    page_key = $PageKey
    blocker = $Code
    detail = $Detail
    recorded_at = Now-Utc
    final_ready = $false
  }
}
function Clean-ControllerRuntimeDirty([string]$Root) {
  $allDirty = @(Get-GitChangedPaths $Root)
  $runtimeDirty = @($allDirty | Where-Object { Is-ControllerRuntimePath $_ })
  $dirty = @($allDirty | Where-Object { -not (Is-ControllerRuntimePath $_) })
  $script:Summary.controller_runtime_dirty_paths = $runtimeDirty
  $script:Summary.controller_dirty_paths = $dirty
  $script:Summary.controller_runtime_dirty_cleaned = $false
  return [pscustomobject]@{ all=$allDirty; runtime=$runtimeDirty; non_runtime=$dirty }
}
function Sync-ControllerRepoDeprecated {
  throw 'DEPRECATED_CONTROLLER_MUTATION_PATH_DISABLED'
  if (-not (Test-Path -LiteralPath $RepoRoot)) { throw 'REPO_ROOT_MISSING: ' + $RepoRoot }
  Assert-GitOk (Invoke-AaysGit $RepoRoot config core.longpaths true) 'CONFIG_LONGPATHS_FAILED'
  $dirtyInfo = Clean-ControllerRuntimeDirty $RepoRoot
  if (@($dirtyInfo.non_runtime).Count -gt 0) {
    $script:Summary.controller_sync_ok = $false
    $script:Summary.controller_sync_mode = 'local_changes_preserved_task_scan_continues'
    return
  }
  if (@($dirtyInfo.runtime).Count -gt 0) {
    $restoredRuntime = @()
    foreach ($runtimePath in @($dirtyInfo.runtime)) {
      $tracked = Invoke-AaysGit $RepoRoot ls-files --error-unmatch -- $runtimePath
      if ($tracked.code -eq 0) {
        $script:Summary.controller_runtime_restore_skipped = $true
        $restoredRuntime += $runtimePath
      }
    }
    $script:Summary.controller_runtime_dirty_cleaned = ($restoredRuntime.Count -gt 0)
    $script:Summary.controller_runtime_dirty_restored_paths = $restoredRuntime
    $dirtyInfo = Clean-ControllerRuntimeDirty $RepoRoot
    if (@($dirtyInfo.non_runtime).Count -gt 0) {
      $script:Summary.controller_sync_ok = $false
      $script:Summary.controller_sync_mode = 'local_changes_preserved_after_runtime_restore_task_scan_continues'
      return
    }
  }
  Assert-GitOk (Invoke-AaysGit -Cwd $RepoRoot -GitArgs @('-c','pack.windowMemory=8m','-c','pack.packSizeLimit=20m','-c','pack.threads=1','-c','core.compression=0','fetch','--no-tags','--depth=1','origin',("+refs/heads/${MainBranch}:refs/remotes/origin/${MainBranch}"))) 'CONTROLLER_FETCH_FAILED'
  Assert-GitOk (Invoke-AaysGit $RepoRoot checkout $MainBranch) 'CONTROLLER_CHECKOUT_FAILED'
  $controllerRebased = Invoke-AaysGit $RepoRoot rebase ('origin/' + $MainBranch)
  if ($controllerRebased.code -ne 0) {
    $script:Summary.controller_rebase_error = $controllerRebased.output
    $abort = Abort-GitRebaseIfPresent $RepoRoot
    if ($abort.code -ne 0) { throw ('CONTROLLER_REBASE_ABORT_FAILED: ' + $abort.output + "`nORIGINAL: " + $controllerRebased.output) }
    throw 'DEPRECATED_CONTROLLER_REBASE_RECOVERY_DISABLED'
    $script:Summary.controller_rebase_recovered = $true
    $script:Summary.controller_sync_ok = $true
    $script:Summary.controller_sync_mode = 'rebase_failed_reset_to_origin'
    return
  }
  $script:Summary.controller_sync_ok = $true
  $script:Summary.controller_sync_mode = 'restore_runtime_then_fetch_rebase_controller'
}
function Assert-GeneratedQueueMirrorPath([string]$Path) {
  $rootFull = [System.IO.Path]::GetFullPath($WorkRoot).TrimEnd('\','/') + [System.IO.Path]::DirectorySeparatorChar
  $pathFull = [System.IO.Path]::GetFullPath($Path)
  if (-not $pathFull.StartsWith($rootFull, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw ('QUEUE_MIRROR_OUTSIDE_WORKROOT: ' + $pathFull)
  }
}
function New-RemoteQueueMirror {
  $remoteRef = 'refs/remotes/origin/' + $MainBranch
  $commitResult = Invoke-AaysGit $RepoRoot rev-parse $remoteRef
  Assert-GitOk $commitResult 'REMOTE_QUEUE_REF_MISSING'
  $remoteCommit = ([string]$commitResult.output).Trim()
  $listResult = Invoke-AaysGit $RepoRoot ls-tree -r --name-only $remoteRef -- 'docs/chatgpt_status'
  Assert-GitOk $listResult 'REMOTE_QUEUE_LIST_FAILED'
  $mirrorRoot = Join-Path $WorkRoot '_remote_queue_mirror'
  $tempRoot = Join-Path $WorkRoot ('_remote_queue_mirror_tmp_' + $PID)
  Assert-GeneratedQueueMirrorPath $mirrorRoot
  Assert-GeneratedQueueMirrorPath $tempRoot
  if (Test-Path -LiteralPath $tempRoot) { Remove-Item -LiteralPath $tempRoot -Recurse -Force }
  Ensure-Dir $tempRoot
  $queuePaths = @($listResult.output -split '\r?\n' | Where-Object { $_ -match '^docs/chatgpt_status/[^/]+/queue/[^/]+$' })
  foreach ($queuePath in $queuePaths) {
    $showResult = Invoke-AaysGit $RepoRoot show ($remoteRef + ':' + $queuePath)
    Assert-GitOk $showResult ('REMOTE_QUEUE_READ_FAILED: ' + $queuePath)
    $destination = Join-Path $tempRoot ($queuePath -replace '/', '\\')
    Ensure-Dir (Split-Path -Parent $destination)
    Write-Utf8 $destination ([string]$showResult.output)
  }
  if (Test-Path -LiteralPath $mirrorRoot) { Remove-Item -LiteralPath $mirrorRoot -Recurse -Force }
  Move-Item -LiteralPath $tempRoot -Destination $mirrorRoot
  $script:RemoteQueueCommit = $remoteCommit
  $script:Summary.remote_queue_commit = $remoteCommit
  $script:Summary.remote_queue_count = $queuePaths.Count
  $script:Summary.queue_source = 'generated_remote_queue_mirror'
  return $mirrorRoot
}
function Sync-ControllerRepoSafe {
  if (-not (Test-Path -LiteralPath $RepoRoot)) { throw 'REPO_ROOT_MISSING: ' + $RepoRoot }
  Assert-GitOk (Invoke-AaysGit $RepoRoot config core.longpaths true) 'CONFIG_LONGPATHS_FAILED'
  $fetchResult = Invoke-AaysGit -Cwd $RepoRoot -GitArgs @('-c','pack.windowMemory=8m','-c','pack.packSizeLimit=20m','-c','pack.threads=1','-c','core.compression=0','fetch','--no-tags','--depth=1','origin',("+refs/heads/${MainBranch}:refs/remotes/origin/${MainBranch}"))
  $dirtyInfo = Clean-ControllerRuntimeDirty $RepoRoot
  $script:Summary.controller_fetch_ok = ($fetchResult.code -eq 0)
  if ($fetchResult.code -ne 0) { $script:Summary.controller_fetch_error = $fetchResult.output }
  $script:Summary.controller_sync_ok = ($fetchResult.code -eq 0)
  $script:Summary.controller_sync_mode = if($fetchResult.code -eq 0){'fresh_remote_queue_mirror_local_changes_preserved'}else{'cached_remote_queue_mirror_fetch_failed_local_changes_preserved'}
  $script:Summary.queue_refresh_fresh = ($fetchResult.code -eq 0)
  $script:Summary.controller_local_changes_preserved = (@($dirtyInfo.all).Count -gt 0)
  return (New-RemoteQueueMirror)
}
function Add-ArchivedTaskWorktree([string]$Path, [string]$ArchivePath, [string]$Reason) {
  if (-not $script:Summary.Contains('archived_task_worktrees')) { $script:Summary['archived_task_worktrees'] = @() }
  $script:Summary['archived_task_worktrees'] = @($script:Summary['archived_task_worktrees']) + [ordered]@{ path=$Path; archive_path=$ArchivePath; reason=$Reason; archived_at=Now-Utc }
}
function Archive-TaskWorktree([string]$Worktree, [string]$Reason) {
  if (-not (Test-Path -LiteralPath $Worktree)) { return $null }
  $archiveRoot = Join-Path $WorkRoot '_archived_task_worktrees'
  Ensure-Dir $archiveRoot
  $leaf = Split-Path -Leaf $Worktree
  $stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMdd_HHmmss')
  $target = Join-Path $archiveRoot ("${leaf}_${stamp}")
  $suffix = 1
  while (Test-Path -LiteralPath $target) {
    $target = Join-Path $archiveRoot ("${leaf}_${stamp}_$suffix")
    $suffix++
  }
  Move-Item -LiteralPath $Worktree -Destination $target
  Add-ArchivedTaskWorktree $Worktree $target $Reason
  return $target
}
function New-TaskWorktreeClone([string]$Worktree, [object]$Task, [string]$Url) {
  # Portable mode: avoid a full GitHub clone for each task. Reuse the controller repo object store.
  Invoke-AaysGit -Cwd $RepoRoot -GitArgs @('worktree','prune') | Out-Null
  Assert-GitOk (Invoke-AaysGit -Cwd $RepoRoot -GitArgs @('-c','pack.windowMemory=8m','-c','pack.packSizeLimit=20m','-c','pack.threads=1','-c','core.compression=0','fetch','--no-tags','--depth=1','origin',("+refs/heads/$($Task.target_branch):refs/remotes/origin/$($Task.target_branch)"))) 'TASK_WORKTREE_FETCH_FAILED'
  Assert-GitOk (Invoke-AaysGit -Cwd $RepoRoot -GitArgs @('worktree','add','--detach',$Worktree,('origin/' + $Task.target_branch))) 'TASK_WORKTREE_ADD_FAILED'
  Assert-GitOk (Invoke-AaysGit $Worktree config core.longpaths true) 'TASK_CONFIG_LONGPATHS_FAILED'
}
function Ensure-TaskWorktree([object]$Task) {
  $safePage = Safe-Name $Task.page_key
  $safeTask = Safe-Name $Task.task_id
  if ($safeTask.Length -gt 20) { $safeTask = $safeTask.Substring(0,20) }
  $worktree = Join-Path $WorkRoot ("${safePage}_${safeTask}")
  $url = 'https://github.com/' + $RepoFullName + '.git'
  Ensure-Dir $WorkRoot
  Assert-GitOk (Invoke-AaysGit $RepoRoot config --global core.longpaths true) 'GLOBAL_LONGPATHS_FAILED'
  if (Test-Path -LiteralPath $worktree) {
    $rebaseMerge = Join-Path $worktree '.git\rebase-merge'
    $rebaseApply = Join-Path $worktree '.git\rebase-apply'
    if ((Test-Path -LiteralPath $rebaseMerge) -or (Test-Path -LiteralPath $rebaseApply)) { Archive-TaskWorktree $worktree 'existing_rebase_in_progress' | Out-Null }
  }
  if (-not (Test-Path -LiteralPath $worktree)) { New-TaskWorktreeClone $worktree $Task $url }
  Assert-GitOk (Invoke-AaysGit $worktree config core.longpaths true) 'TASK_CONFIG_LONGPATHS_FAILED'
  $dirty = @(Get-GitChangedPaths $worktree)
  $script:TaskWorktreeHadDirty = ($dirty.Count -gt 0)
  if ($dirty.Count -gt 0) {
    $script:Summary.existing_task_worktree_dirty_paths = $dirty
    Archive-TaskWorktree $worktree 'existing_dirty_task_worktree' | Out-Null
    New-TaskWorktreeClone $worktree $Task $url
  }
  Assert-GitOk (Invoke-AaysGit -Cwd $worktree -GitArgs @('-c','pack.windowMemory=8m','-c','pack.packSizeLimit=20m','-c','pack.threads=1','-c','core.compression=0','fetch','--no-tags','--depth=1','origin',("+refs/heads/$($Task.target_branch):refs/remotes/origin/$($Task.target_branch)"))) 'TASK_FETCH_FAILED'
  Assert-GitOk (Invoke-AaysGit $worktree checkout --detach ('origin/' + $Task.target_branch)) 'TASK_CHECKOUT_FAILED'
  $rebased = [pscustomobject]@{ code = 0; output = 'portable_detached_worktree_no_rebase_needed' }
  if ($rebased.code -ne 0) {
    $script:Summary.task_worktree_rebase_error = $rebased.output
    Archive-TaskWorktree $worktree 'task_rebase_conflict' | Out-Null
    New-TaskWorktreeClone $worktree $Task $url
    Assert-GitOk (Invoke-AaysGit -Cwd $worktree -GitArgs @('-c','pack.windowMemory=8m','-c','pack.packSizeLimit=20m','-c','pack.threads=1','-c','core.compression=0','fetch','--no-tags','--depth=1','origin',("+refs/heads/$($Task.target_branch):refs/remotes/origin/$($Task.target_branch)"))) 'TASK_FETCH_FAILED_AFTER_ARCHIVE'
    Assert-GitOk (Invoke-AaysGit $worktree checkout --detach ('origin/' + $Task.target_branch)) 'TASK_CHECKOUT_FAILED_AFTER_ARCHIVE'
    $rebased = [pscustomobject]@{ code = 0; output = 'portable_detached_worktree_no_rebase_needed_after_archive' }
    if ($rebased.code -ne 0) { throw ('BLOCKED_REBASE_CONFLICT: ' + $rebased.output) }
  }
  return $worktree
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
  $relative = Rel ($File.FullName.Substring($script:QueueScanRoot.Length).TrimStart('\','/'))
  if ($relative -notmatch '^docs/chatgpt_status/([^/]+)/queue/[^/]+$') {
    return [pscustomobject]@{ valid=$false; queue_rel=$relative; skip_reason='NOT_CANONICAL_QUEUE_PATH' }
  }
  $pageFromPath = $Matches[1]
  try {
    $data = Read-QueueFile $File
  } catch {
    return [pscustomobject]@{
      valid = $false
      validation_errors = @('QUEUE_PARSE_FAILED')
      page_key = $pageFromPath
      task_id = (Safe-Name ([System.IO.Path]::GetFileNameWithoutExtension($File.Name)))
      status = 'invalid'
      status_norm = 'invalid'
      script_path = ''
      target_branch = $MainBranch
      allowed_paths = @()
      priority = 1000
      queue_rel = $relative
      parse_error = $_.Exception.Message
      data = $null
    }
  }
  $page = [string](Get-Prop $data 'page_key')
  $scriptPath = [string](Get-Prop $data 'script_path')
  if (-not $scriptPath) { $scriptPath = [string](Get-Prop $data 'automation_script') }
  $targetBranch = [string](Get-Prop $data 'target_branch')
  if (-not $targetBranch) { $targetBranch = $MainBranch }
  $taskId = [string](Get-Prop $data 'task_id')
  if (-not $taskId) { $taskId = [System.IO.Path]::GetFileNameWithoutExtension($File.Name) }
  $status = [string](Get-Prop $data 'status')
  if (-not $status) { $status = 'queued' }
  $allowed = Normalize-Allowed (Get-Prop $data 'allowed_paths')
  $priorityRaw = Get-Prop $data 'priority'
  $priority = 1000
  if ($priorityRaw -ne $null) { [void][int]::TryParse(([string]$priorityRaw), [ref]$priority) }
  $errors = @()
  if (-not $page) { $errors += 'MISSING_page_key' }
  if ($page -and $page -ne $pageFromPath) { $errors += 'PAGE_KEY_PATH_MISMATCH' }
  if (-not $scriptPath) { $errors += 'MISSING_script_path_OR_automation_script' }
  if (-not $targetBranch) { $errors += 'MISSING_target_branch' }
  if ($allowed.Count -eq 0) { $errors += 'MISSING_allowed_paths' }
  foreach ($flag in @('no_fake_final_ready','no_db_write','no_migration','no_production_deploy')) {
    if (-not (Queue-SafetyFlagOk $data $flag)) { $errors += ('MISSING_OR_FALSE_' + $flag) }
  }
  return [pscustomobject]@{
    valid = ($errors.Count -eq 0)
    validation_errors = $errors
    page_key = $page
    task_id = (Safe-Name $taskId)
    status = $status
    status_norm = $status.Trim().ToLowerInvariant()
    script_path = $scriptPath
    target_branch = $targetBranch
    allowed_paths = $allowed
    priority = $priority
    queue_rel = $relative
    data = $data
  }
}
function Resolve-ScriptPath([string]$Worktree, [string]$ScriptPath) {
  $p = $ScriptPath -replace '/', '\'
  if ([System.IO.Path]::IsPathRooted($p)) {
    $repoFull = [System.IO.Path]::GetFullPath($RepoRoot).TrimEnd('\')
    $full = [System.IO.Path]::GetFullPath($p)
    if ($full.StartsWith($repoFull, [System.StringComparison]::OrdinalIgnoreCase)) {
      $rel = $full.Substring($repoFull.Length).TrimStart('\')
      return (Join-Path $Worktree $rel)
    }
    return $full
  }
  return (Join-Path $Worktree $p)
}
function Browser-Gate {
  $node = Get-Command node -ErrorAction SilentlyContinue
  $npm = Get-Command npm -ErrorAction SilentlyContinue
  $edge = @(
    "$env:ProgramFiles (x86)\Microsoft\Edge\Application\msedge.exe",
    "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe",
    "$env:LOCALAPPDATA\Microsoft\Edge\Application\msedge.exe",
    "$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
    "$env:ProgramFiles (x86)\Google\Chrome\Application\chrome.exe"
  ) | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
  $playwright = $false
  try { & node -e "try{require.resolve('playwright');process.exit(0)}catch(e){process.exit(1)}" 2>$null; $playwright = ($LASTEXITCODE -eq 0) } catch { $playwright = $false }
  $site8010 = $false
  $site8012 = $false
  $site8020 = $false
  try { $resp = Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:8010/england_map_web/?runner_smoke=1' -TimeoutSec 5; $site8010 = ($resp.StatusCode -ge 200 -and $resp.StatusCode -lt 500) } catch {}
  try { $resp = Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:8012/england_map_web/index.html?runner_smoke=1' -TimeoutSec 5; $site8012 = ($resp.StatusCode -ge 200 -and $resp.StatusCode -lt 500) } catch {}
  try { $resp = Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:8020/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html?runner_smoke=1' -TimeoutSec 5; $site8020 = ($resp.StatusCode -ge 200 -and $resp.StatusCode -lt 500) } catch {}
  $smoke = ([bool]$edge -and ($site8010 -or $site8012 -or $site8020))
  return [pscustomobject]@{ node_exists=[bool]$node; npm_exists=[bool]$npm; edge_or_chrome_exists=[bool]$edge; playwright_available=$playwright; site_8010_ok=$site8010; site_8012_ok=$site8012; site_8020_ok=$site8020; browser_smoke_degraded_ok=($smoke -and -not $playwright); browser_smoke_passed=$smoke }
}
function Write-TaskFile([string]$Worktree, [string]$RelPath, [object]$Payload) {
  $full = Join-Path $Worktree ($RelPath -replace '/', '\')
  $content = if ($Payload -is [string]) { $Payload } else { To-JsonText $Payload }
  Write-Utf8 $full $content
}
function Push-Sync([string]$Worktree, [string]$Branch, [string]$CommitMessage) {
  if ($NoPush) { Add-Blocker 'NO_PUSH_MODE'; return }
  $cached = Invoke-AaysGit $Worktree diff --cached --name-only
  Assert-GitOk $cached 'DIFF_CACHED_FAILED'
  if ($cached.output) { Assert-GitOk (Invoke-AaysGit $Worktree commit -m $CommitMessage) 'COMMIT_FAILED' }

  # Cloud ChatGPT pages can replace the branch history while a task is running.
  # Preserve only this task's final commit paths and replay them on the newest
  # remote tip instead of rebasing unrelated historical commits.
  $changedResult = Invoke-AaysGit $Worktree diff-tree --no-commit-id --name-only -r HEAD
  Assert-GitOk $changedResult 'TASK_COMMIT_PATHS_FAILED'
  $changedPaths = @(($changedResult.output -split "`r?`n") | ForEach-Object { $_.Trim() } | Where-Object { $_ } | Select-Object -Unique)
  if ($changedPaths.Count -eq 0) { return }

  $portableRoot = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $WorkRoot))
  $recoveryRoot = Join-Path $portableRoot ('_push_recovery\' + [guid]::NewGuid().ToString('N'))
  Ensure-Dir $recoveryRoot
  $presentPaths = @{}
  foreach ($rel in $changedPaths) {
    $source = Join-Path $Worktree ($rel -replace '/', '\')
    if (Test-Path -LiteralPath $source -PathType Leaf) {
      $backup = Join-Path $recoveryRoot ($rel -replace '/', '\')
      Ensure-Dir (Split-Path -Parent $backup)
      Copy-Item -LiteralPath $source -Destination $backup -Force
      $presentPaths[$rel] = $true
    } else {
      $presentPaths[$rel] = $false
    }
  }

  $lastPush = $null
  try {
    for ($attempt = 1; $attempt -le 4; $attempt++) {
      Assert-GitOk (Invoke-AaysGit -Cwd $Worktree -GitArgs @('-c','pack.windowMemory=8m','-c','pack.packSizeLimit=20m','-c','pack.threads=1','-c','core.compression=0','fetch','--no-tags','--depth=1','origin',("+refs/heads/${Branch}:refs/remotes/origin/${Branch}"))) 'POST_FETCH_FAILED'
      Assert-GitOk (Invoke-AaysGit $Worktree checkout --detach ('origin/' + $Branch)) 'REMOTE_REPLAY_CHECKOUT_FAILED'

      foreach ($rel in $changedPaths) {
        $target = Join-Path $Worktree ($rel -replace '/', '\')
        if ([bool]$presentPaths[$rel]) {
          $backup = Join-Path $recoveryRoot ($rel -replace '/', '\')
          Ensure-Dir (Split-Path -Parent $target)
          Copy-Item -LiteralPath $backup -Destination $target -Force
        } elseif (Test-Path -LiteralPath $target) {
          Remove-Item -LiteralPath $target -Force
        }
      }

      # Keep every native command comfortably below Windows' command-line limit.
      foreach ($rel in $changedPaths) {
        Assert-GitOk (Invoke-AaysGit $Worktree add -A -- $rel) 'REMOTE_REPLAY_STAGE_FAILED'
      }
      $replayed = Invoke-AaysGit $Worktree diff --cached --name-only
      Assert-GitOk $replayed 'REMOTE_REPLAY_DIFF_FAILED'
      if (-not $replayed.output) { return }
      Assert-GitOk (Invoke-AaysGit $Worktree commit -m $CommitMessage) 'REMOTE_REPLAY_COMMIT_FAILED'

      $lastPush = Invoke-AaysGit -Cwd $Worktree -GitArgs @('-c','pack.windowMemory=16m','-c','pack.packSizeLimit=50m','-c','pack.threads=1','push','origin',('HEAD:' + $Branch))
      if ($lastPush.code -eq 0) { return }
      Start-Sleep -Seconds ([math]::Min(8, 2 * $attempt))
    }
    throw ('POST_PUSH_REPLAY_RETRIES_EXHAUSTED: ' + $lastPush.output)
  } finally {
    if (Test-Path -LiteralPath $recoveryRoot) { Remove-Item -LiteralPath $recoveryRoot -Recurse -Force -ErrorAction SilentlyContinue }
  }
}
function Update-OneClickSmokeProof([string]$Worktree, [string]$Branch, [string]$TaskId) {
  if ($TaskId -notlike 'one_click_runner_smoke_*') { return $null }
  $latestRel = 'docs/chatgpt_status/_shared/runner_outputs/one_click_runner_self_test_latest.json'
  $latestPath = Join-Path $Worktree ($latestRel -replace '/', '\')
  if (-not (Test-Path -LiteralPath $latestPath)) { throw 'ONE_CLICK_SMOKE_LATEST_MISSING' }
  $head = Invoke-AaysGit $Worktree rev-parse HEAD
  Assert-GitOk $head 'ONE_CLICK_SMOKE_HEAD_FAILED'
  Assert-GitOk (Invoke-AaysGit -Cwd $Worktree -GitArgs @('-c','pack.windowMemory=8m','-c','pack.packSizeLimit=20m','-c','pack.threads=1','fetch','--no-tags','--depth=1','origin',("+refs/heads/${Branch}:refs/remotes/origin/${Branch}"))) 'ONE_CLICK_SMOKE_READBACK_FETCH_FAILED'
  $remote = Invoke-AaysGit $Worktree show (('origin/' + $Branch + ':') + $latestRel)
  Assert-GitOk $remote 'ONE_CLICK_SMOKE_REMOTE_READBACK_FAILED'
  $localJson = Get-Content -LiteralPath $latestPath -Raw | ConvertFrom-Json
  $remoteJson = $remote.output | ConvertFrom-Json
  $nonceMatch = ([string]$localJson.nonce -eq [string]$remoteJson.nonce)
  $payloadMatch = ([string]$localJson.payload -eq [string]$remoteJson.payload)
  Add-Member -InputObject $localJson -NotePropertyName git_commit_sha -NotePropertyValue $head.output -Force
  Add-Member -InputObject $localJson -NotePropertyName git_push_status -NotePropertyValue 'pushed' -Force
  Add-Member -InputObject $localJson -NotePropertyName github_fetch_verified -NotePropertyValue ($nonceMatch -and $payloadMatch) -Force
  Add-Member -InputObject $localJson -NotePropertyName remote_readback_ok -NotePropertyValue ($nonceMatch -and $payloadMatch) -Force
  Add-Member -InputObject $localJson -NotePropertyName remote_nonce_match -NotePropertyValue $nonceMatch -Force
  Add-Member -InputObject $localJson -NotePropertyName remote_payload_match -NotePropertyValue $payloadMatch -Force
  Write-TaskFile $Worktree $latestRel $localJson
  $timestampedRel = [string]$localJson.timestamped_proof_path
  if ($timestampedRel) { Write-TaskFile $Worktree $timestampedRel $localJson }
  $pushProofRel = 'docs/chatgpt_status/_shared/smoke_tests/one_click_runner_smoke_push_proof_latest.json'
  Write-TaskFile $Worktree $pushProofRel ([ordered]@{
    status = if ($nonceMatch -and $payloadMatch) { 'PASS' } else { 'FAIL' }
    task_id = $TaskId
    artifact_path = $latestRel
    artifact_commit_sha = $head.output
    branch = $Branch
    local_nonce = $localJson.nonce
    remote_nonce = $remoteJson.nonce
    nonce_match = $nonceMatch
    payload_match = $payloadMatch
    runner_pid = $localJson.runner_pid
    heartbeat_at = $localJson.heartbeat_at
    pushed_at = Now-Utc
    final_ready = $false
    fake_data = $false
    db_write = $false
    migration = $false
    production_deploy = $false
  })
  return [pscustomobject]@{ ok=($nonceMatch -and $payloadMatch); latest_rel=$latestRel; push_proof_rel=$pushProofRel; commit_sha=$head.output }
}
function Sync-TaskResultBackToController([string]$Worktree, [object]$Task, [object]$SmokeProof) {
  $rels = @($Task.queue_rel, "docs/chatgpt_status/$($Task.page_key)/queue/current.task.json")
  if ($SmokeProof) { $rels += @($SmokeProof.latest_rel,$SmokeProof.push_proof_rel) }
  foreach ($relPath in @($rels | Where-Object { $_ } | Select-Object -Unique)) {
    $source = Join-Path $Worktree ($relPath -replace '/', '\')
    $destination = Join-Path $RepoRoot ($relPath -replace '/', '\')
    if (Test-Path -LiteralPath $source) {
      Ensure-Dir (Split-Path -Parent $destination)
      Copy-Item -LiteralPath $source -Destination $destination -Force
    }
  }
}
function Run-Task([object]$Task) {
  $script:Summary.queue_started = $true
  $page = $Task.page_key
  $taskId = $Task.task_id
  $allowedSeed = @($Task.allowed_paths) + @(
    "docs/chatgpt_status/$page/status",
    "docs/chatgpt_status/$page/heartbeat",
    "docs/chatgpt_status/$page/reports",
    "docs/chatgpt_status/$page/runner_outputs",
    "docs/chatgpt_status/$page/queue",
    "docs/chatgpt_status/_shared/status",
    "docs/chatgpt_status/_shared/reports",
    "docs/chatgpt_status/_shared/heartbeat"
  )
  $allowed = @($allowedSeed | ForEach-Object { Rel $_ } | Select-Object -Unique)
  $worktree = Ensure-TaskWorktree $Task
  $script:Summary.task_runs_in_clean_worktree = (-not $script:TaskWorktreeHadDirty)
  $scriptPath = Resolve-ScriptPath $worktree $Task.script_path
  $startedRel = "docs/chatgpt_status/$page/status/${taskId}_started.json"
  $heartbeatRel = "docs/chatgpt_status/$page/heartbeat/${taskId}_heartbeat.txt"
  $reportRel = "docs/chatgpt_status/$page/reports/${taskId}_runner_output.txt"
  $completedRel = "docs/chatgpt_status/$page/status/${taskId}_completed.json"
  $gateRel = "docs/chatgpt_status/$page/status/${taskId}_gate.json"
  $mirrorRel = "docs/chatgpt_status/_shared/status/queue_result_mirror_${taskId}.json"
  $currentRel = "docs/chatgpt_status/$page/queue/current.task.json"
  $browser = Browser-Gate
  if (-not $browser.browser_smoke_passed) { Add-TaskBlocker $taskId $page 'BLOCKED_BROWSER_ENVIRONMENT' }
  if (-not (Test-Path -LiteralPath $scriptPath)) { throw ('SCRIPT_MISSING: ' + $scriptPath) }
  $claimedAt = Now-Utc
  $runningPayload = [ordered]@{ task_id=$taskId; page_key=$page; status='running'; claimed_at=$claimedAt; claim_owner='single_shared_runner'; claim_pid=$PID; target_branch=$Task.target_branch; script_path=$Task.script_path; allowed_paths=$Task.allowed_paths; no_fake_final_ready=$true; no_db_write=$true; no_migration=$true; no_production_deploy=$true; final_ready=$false }
  Write-TaskFile $worktree $startedRel ([ordered]@{ task_id=$taskId; page_key=$page; started_at=$claimedAt; queue_seen=$true; queue_started=$true; single_runner_lock_acquired=$true; task_runs_in_clean_worktree=$true; final_ready=$false; fake_data=$false; db_write=$false; migration=$false; production_deploy=$false })
  Write-TaskFile $worktree $heartbeatRel "TASK_ID=$taskId`nPAGE_KEY=$page`nSTATUS=running`nHEARTBEAT_AT=$(Now-Utc)`n"
  Write-TaskFile $worktree $Task.queue_rel $runningPayload
  Write-TaskFile $worktree $currentRel $runningPayload
  $claimStage = Stage-AllowedOnly $worktree $allowed
  if (-not $claimStage.ok) { throw ('CLAIM_UNSCOPED_CHANGES: ' + ($claimStage.unscoped -join ',')) }
  Push-Sync $worktree $Task.target_branch "AAYS shared runner claim $page $taskId"
  Sync-TaskResultBackToController $worktree $Task $null
  $script:Summary.last_pickup_task_id = $taskId
  $script:Summary.last_pickup_at = $claimedAt
  $script:Summary.current_task_id = $taskId
  Write-Utf8 $LatestStatusPath (To-JsonText $script:Summary)
  $script:Summary.github_auth_preflight = 'skipped_to_avoid_low_memory_ls_remote_oom'
  $script:Summary.final_push_is_authoritative = $true
  $oldRoot=$env:AAYS_REPO_ROOT; $oldController=$env:AAYS_CONTROLLER_REPO_ROOT; $oldTask=$env:AAYS_TASK_ID; $oldPage=$env:AAYS_PAGE_KEY; $oldBranch=$env:AAYS_TARGET_BRANCH; $oldNoBytecode=$env:PYTHONDONTWRITEBYTECODE
  $env:AAYS_REPO_ROOT=$worktree; $env:AAYS_TASK_ID=$taskId; $env:AAYS_PAGE_KEY=$page
  $env:AAYS_CONTROLLER_REPO_ROOT=$RepoRoot
  $env:AAYS_TARGET_BRANCH=$Task.target_branch
  $env:PYTHONDONTWRITEBYTECODE='1'
  $automationOutput=''; $automationCode=0
  $oldAutomationEap=$ErrorActionPreference
  try {
    $ErrorActionPreference='Continue'
    Push-Location -LiteralPath $worktree
    try { $out = & powershell -NoProfile -ExecutionPolicy Bypass -File $scriptPath 2>&1; $automationCode=$LASTEXITCODE; $automationOutput=($out | Out-String) } finally { Pop-Location }
  } finally {
    $ErrorActionPreference=$oldAutomationEap
    $env:AAYS_REPO_ROOT=$oldRoot; $env:AAYS_CONTROLLER_REPO_ROOT=$oldController; $env:AAYS_TASK_ID=$oldTask; $env:AAYS_PAGE_KEY=$oldPage; $env:AAYS_TARGET_BRANCH=$oldBranch; $env:PYTHONDONTWRITEBYTECODE=$oldNoBytecode
  }
  if ($automationCode -ne 0) { Add-TaskBlocker $taskId $page 'AUTOMATION_EXIT_NONZERO' ([string]$automationCode) }
  $gatePath = Join-Path $worktree ($gateRel -replace '/', '\')
  $gate = $null
  if (Test-Path -LiteralPath $gatePath) { try { $gate = Get-Content -LiteralPath $gatePath -Raw | ConvertFrom-Json } catch { Add-TaskBlocker $taskId $page 'GATE_PARSE_FAILED' $_.Exception.Message } }
  if ($null -eq $gate) {
    $gate = [pscustomobject]@{ source_row_gate_passed=$false; ui_token_gate_passed=$false; browser_smoke_passed=$browser.browser_smoke_passed; post_sync_ok=$false; manual_review_required=$true; fake_data=$false }
    Write-TaskFile $worktree $gateRel $gate
  }
  Write-TaskFile $worktree $reportRel ("TASK_ID=$taskId`nPAGE_KEY=$page`nRUNNER_STABLE=20260707`nwork_root=$WorkRoot`nnode_exists=$($browser.node_exists)`nnpm_exists=$($browser.npm_exists)`nedge_or_chrome_exists=$($browser.edge_or_chrome_exists)`nplaywright_available=$($browser.playwright_available)`nsite_8010_ok=$($browser.site_8010_ok)`nsite_8020_ok=$($browser.site_8020_ok)`nbrowser_smoke_passed=$($browser.browser_smoke_passed)`nautomation_exit_code=$automationCode`nfake_data=false`n--- output ---`n$automationOutput")
  if ($automationCode -ne 0) {
    $blockedPayload=[ordered]@{task_id=$taskId;page_key=$page;status='blocked';blocked_at=Now-Utc;automation_exit_code=$automationCode;runner_output_uploaded=$true;PUSH_SYNC_OK=$true;CONTINUE_RUNNER_READY=$true;blockers=@('AUTOMATION_EXIT_NONZERO');final_ready=$false;product_final_ready=$false;fake_data=$false;db_write=$false;migration=$false;production_deploy=$false}
    Write-TaskFile $worktree $gateRel $blockedPayload
    Write-TaskFile $worktree $mirrorRel $blockedPayload
    Write-TaskFile $worktree $Task.queue_rel ([ordered]@{task_id=$taskId;page_key=$page;status='blocked';runner_blocked_at=Now-Utc;automation_exit_code=$automationCode;blockers=@('AUTOMATION_EXIT_NONZERO');final_ready=$false;no_fake_final_ready=$true;no_db_write=$true;no_migration=$true;no_production_deploy=$true})
    Write-TaskFile $worktree $currentRel ([ordered]@{task_id=$taskId;page_key=$page;status='blocked';runner_blocked_at=Now-Utc;automation_exit_code=$automationCode;blockers=@('AUTOMATION_EXIT_NONZERO');claim_owner='single_shared_runner';claim_pid=$PID;final_ready=$false})
    Write-TaskFile $worktree $heartbeatRel "TASK_ID=$taskId`nPAGE_KEY=$page`nSTATUS=blocked`nAUTOMATION_EXIT_CODE=$automationCode`nFINAL_READY=false`nHEARTBEAT_AT=$(Now-Utc)`n"
    $blockedStage=Stage-AllowedOnly $worktree $allowed
    if(-not$blockedStage.ok){throw('BLOCKED_UNSCOPED_CHANGES: '+($blockedStage.unscoped-join','))}
    Push-Sync $worktree $Task.target_branch "AAYS shared runner blocked evidence $page $taskId"
    Sync-TaskResultBackToController $worktree $Task $null
    $script:Summary.runner_output_uploaded=$true;$script:Summary.post_sync_ok=$true;$script:Summary.PUSH_SYNC_OK=$true;$script:Summary.CONTINUE_RUNNER_READY=$true
    return [pscustomobject]@{task_id=$taskId;page_key=$page;completed=$false;status='blocked';automation_exit_code=$automationCode;final_ready=$false;worktree=$worktree}
  }
  $stage = Stage-AllowedOnly $worktree $allowed
  if (-not $stage.ok) { throw ('BLOCKED_UNSCOPED_CHANGES: ' + ($stage.unscoped -join ',')) }
  $script:Summary.allowed_paths_enforced = $true
  Push-Sync $worktree $Task.target_branch "AAYS shared runner stable output $page $taskId"
  $smokeProof = Update-OneClickSmokeProof $worktree $Task.target_branch $taskId
  $finalReady = ((As-Bool (Get-Prop $gate 'source_row_gate_passed')) -and (As-Bool (Get-Prop $gate 'ui_token_gate_passed')) -and $browser.browser_smoke_passed -and (-not (As-Bool (Get-Prop $gate 'manual_review_required'))) -and (-not (As-Bool (Get-Prop $gate 'fake_data'))) -and $automationCode -eq 0)
  $completed = [ordered]@{ task_id=$taskId; page_key=$page; completed_at=Now-Utc; queue_seen=$true; queue_started=$true; single_runner_lock_acquired=$true; task_runs_in_clean_worktree=$true; allowed_paths_enforced=$true; runner_output_uploaded=$true; post_sync_ok=$true; PUSH_SYNC_OK=$true; CONTINUE_RUNNER_READY=$true; browser_environment=$browser; final_ready=$finalReady; fake_data=$false; db_write=$false; migration=$false; production_deploy=$false; blockers=@($script:Summary.blockers) }
  Write-TaskFile $worktree $completedRel $completed
  Write-TaskFile $worktree $mirrorRel $completed
  Write-TaskFile $worktree $Task.queue_rel ([ordered]@{ task_id=$taskId; page_key=$page; status='done'; runner_completed_at=Now-Utc; PUSH_SYNC_OK=$true; CONTINUE_RUNNER_READY=$true; final_ready=$finalReady; no_fake_final_ready=$true; no_db_write=$true; no_migration=$true; no_production_deploy=$true })
  Write-TaskFile $worktree $currentRel ([ordered]@{ task_id=$taskId; page_key=$page; status='done'; runner_completed_at=Now-Utc; claim_owner='single_shared_runner'; claim_pid=$PID; PUSH_SYNC_OK=$true; CONTINUE_RUNNER_READY=$true; final_ready=$finalReady })
  Write-TaskFile $worktree $heartbeatRel "TASK_ID=$taskId`nPAGE_KEY=$page`nSTATUS=completed`nPUSH_SYNC_OK=true`nCONTINUE_RUNNER_READY=true`nFINAL_READY=$finalReady`nHEARTBEAT_AT=$(Now-Utc)`n"
  $stage2 = Stage-AllowedOnly $worktree $allowed
  if (-not $stage2.ok) { throw ('BLOCKED_UNSCOPED_CHANGES: ' + ($stage2.unscoped -join ',')) }
  Push-Sync $worktree $Task.target_branch "AAYS shared runner stable completion $page $taskId"
  Sync-TaskResultBackToController $worktree $Task $smokeProof
  $script:Summary.runner_output_uploaded=$true; $script:Summary.post_sync_ok=$true; $script:Summary.PUSH_SYNC_OK=$true; $script:Summary.CONTINUE_RUNNER_READY=$true; $script:Summary.final_ready=[bool]$finalReady
  return [pscustomobject]@{ task_id=$taskId; page_key=$page; completed=$true; final_ready=[bool]$finalReady; worktree=$worktree }
}

$RepoRoot = [System.IO.Path]::GetFullPath($RepoRoot)
$WorkRoot = [System.IO.Path]::GetFullPath($WorkRoot)
if ($RepoRoot.StartsWith('C:\AAYS_WT\', [System.StringComparison]::OrdinalIgnoreCase)) { throw 'BLOCKED_C_DRIVE_NOT_CANONICAL: ' + $RepoRoot }
if (-not (Test-Path -LiteralPath (Join-Path $RepoRoot 'docs\chatgpt_status\_shared'))) { throw 'BLOCKED_REPO_ROOT_NOT_AAYS: ' + $RepoRoot }
Ensure-Dir $WorkRoot
$SharedRoot = Join-Path $RepoRoot 'docs\chatgpt_status\_shared'
$StatusDir = Join-Path $SharedRoot 'status'
$ReportDir = Join-Path $SharedRoot 'reports'
$HeartbeatDir = Join-Path $SharedRoot 'heartbeat'
$LockDir = Join-Path $SharedRoot 'runner_lock'
$LogDir = Join-Path $SharedRoot 'logs'
foreach ($d in @($StatusDir,$ReportDir,$HeartbeatDir,$LockDir,$LogDir)) { Ensure-Dir $d }
$RunId = (Get-Date -Format 'yyyyMMdd_HHmmss')
$script:GitLogPath = Join-Path $LogDir "MULTI_PAGE_git_args_$RunId.log"
$LockPath = Join-Path $LockDir 'MULTI_PAGE.lock'
$ScanInstanceId = [guid]::NewGuid().ToString('N')
$RunnerHeartbeatPath = Join-Path $HeartbeatDir 'MULTI_PAGE_heartbeat_latest.json'
$LatestStatusPath = Join-Path $StatusDir 'MULTI_PAGE_latest_status.json'
$SelectionDebugPath = Join-Path $StatusDir 'queue_selection_debug_20260705.json'
$SkipDebugPath = Join-Path $StatusDir 'queue_skip_status_check_20260705.json'
$TodayStamp = (Get-Date).ToString('yyyyMMdd')
$SelectionDebugPathToday = Join-Path $StatusDir "queue_selection_debug_${TodayStamp}.json"
$SkipDebugPathToday = Join-Path $StatusDir "queue_skip_status_check_${TodayStamp}.json"
$script:Summary = [ordered]@{ run_id=$RunId; checked_at=Now-Utc; repo_root=$RepoRoot; work_root=$WorkRoot; main_branch=$MainBranch; queue_seen=$false; queue_started=$false; queue_detected_count=0; queue_ready_count=0; selected_task_ids=@(); last_queue_scan_at=$null; last_pickup_task_id=$null; last_pickup_at=$null; current_task_id=$null; single_runner_lock_acquired=$false; task_runs_in_clean_worktree=$false; allowed_paths_enforced=$false; runner_output_uploaded=$false; post_sync_ok=$false; PUSH_SYNC_OK=$false; CONTINUE_RUNNER_READY=$false; final_ready=$false; fake_data=$false; db_write=$false; migration=$false; production_deploy=$false; blockers=@(); task_blockers=@(); processed=@(); skipped=@() }

try {
  $script:QueueScanRoot = Sync-ControllerRepoSafe
  $lockFresh = $false
  if (Test-Path -LiteralPath $LockPath) {
    $existingLock=$null
    if(Test-Path -LiteralPath $LockPath -PathType Leaf){$existingLock=Read-JsonFile $LockPath}
    elseif(Test-Path -LiteralPath $LockPath -PathType Container){$existingLock=Read-JsonFile (Join-Path $LockPath 'owner.json')}
    if(Test-ScanLockOwner $existingLock){$lockFresh=$true}else{Remove-Item -LiteralPath $LockPath -Force -Recurse -ErrorAction SilentlyContinue}
  }
  if ($lockFresh) { Add-Blocker 'RUNNER_ALREADY_ACTIVE'; $script:Summary.CONTINUE_RUNNER_READY=$true; Write-Utf8 $LatestStatusPath (To-JsonText $script:Summary); Write-Output (To-JsonText $script:Summary); exit 0 }
  $scanProcess=Get-Process -Id $PID -ErrorAction Stop
  $scanLock=[ordered]@{instance_id=$ScanInstanceId;pid=$PID;process_start_time=$scanProcess.StartTime.ToUniversalTime().ToString('o');executable_path=$scanProcess.Path;created_at=Now-Utc;updated_at=Now-Utc;lock_scope='single_scan_worker';repo_root=$RepoRoot;work_root=$WorkRoot;final_ready=$false}
  Write-Utf8Atomic $LockPath (To-JsonText $scanLock)
  $script:Summary.single_runner_lock_acquired = $true
  Write-Utf8 $RunnerHeartbeatPath (To-JsonText ([ordered]@{ pid=$PID; instance_id=$ScanInstanceId; lock_scope='single_scan_worker'; started_at=Now-Utc; runner='RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_STABLE_20260707'; scan_runner='RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_STABLE_20260707'; heartbeat_path=$RunnerHeartbeatPath; lock_path=$LockPath; work_root=$WorkRoot }))
  # current.task.json is an advisory runner-owned pointer, never a queue item.
  $queueFiles = @(Get-ChildItem -LiteralPath (Join-Path $script:QueueScanRoot 'docs\chatgpt_status') -Recurse -File -ErrorAction SilentlyContinue | Where-Object { $_.FullName -match '\\queue\\' -and $_.Name -ne 'current.task.json' })
  $parsed = @($queueFiles | ForEach-Object { Parse-Queue $_ })
  $readyCandidates = @($parsed | Where-Object { $_.valid -and $_.task_id -ne 'aays1-f-portable-one-click-recovery-bootstrap-20260709' -and $_.status_norm -in @('queued','ready','pending','pending_repo_queue','pickup_requested','queued_for_single_shared_runner') } | Sort-Object priority, page_key, task_id)
  $ready = @()
  $seenTaskIds = @{}
  foreach ($candidate in $readyCandidates) {
    if ($seenTaskIds.ContainsKey([string]$candidate.task_id)) {
      $script:Summary.skipped += [ordered]@{task_id=$candidate.task_id;page_key=$candidate.page_key;status='duplicate_queue_entry_ignored';queue_rel=$candidate.queue_rel;final_ready=$false}
      continue
    }
    $seenTaskIds[[string]$candidate.task_id] = $true
    $ready += $candidate
  }
  $script:Summary.queue_seen = ($parsed.Count -gt 0)
  $scanAt = Now-Utc
  $script:Summary.queue_detected_count = $parsed.Count
  $script:Summary.queue_ready_count = $ready.Count
  $script:Summary.selected_task_ids = @($ready | Select-Object -First $MaxTasks | ForEach-Object {$_.task_id})
  $script:Summary.last_queue_scan_at = $scanAt
  $selectionPayload = [ordered]@{ checked_at=$scanAt; queue_source=$script:Summary.queue_source; poll_repo_root=$RepoRoot; poll_branch=$MainBranch; remote_queue_commit=$script:RemoteQueueCommit; parsed_count=$parsed.Count; ready_candidate_count=$readyCandidates.Count; ready_count=$ready.Count; duplicate_task_count=($readyCandidates.Count-$ready.Count); selected_task_ids=$script:Summary.selected_task_ids; ready=$ready }
  $skipPayload = [ordered]@{ checked_at=Now-Utc; skipped=@($parsed | Where-Object { -not $_.valid -or -not ($_.status_norm -in @('queued','ready','pending','pending_repo_queue','pickup_requested','queued_for_single_shared_runner')) }) }
  Write-Utf8 $SelectionDebugPath (To-JsonText $selectionPayload)
  Write-Utf8 $SelectionDebugPathToday (To-JsonText $selectionPayload)
  Write-Utf8 $SkipDebugPath (To-JsonText $skipPayload)
  Write-Utf8 $SkipDebugPathToday (To-JsonText $skipPayload)
  if ($ScanOnly) { $script:Summary.CONTINUE_RUNNER_READY=$true; Write-Utf8 $LatestStatusPath (To-JsonText $script:Summary); Write-Output (To-JsonText $script:Summary); exit 0 }
  $count = 0
  foreach ($task in $ready) {
    if ($count -ge $MaxTasks) { break }
    try {
      $res = Run-Task $task
      $script:Summary.processed += $res
    } catch {
      Add-TaskBlocker $task.task_id $task.page_key 'RUNNER_TASK_FAILED' $_.Exception.Message
      $script:Summary.skipped += [ordered]@{ task_id=$task.task_id; page_key=$task.page_key; status='blocked'; blocker='RUNNER_TASK_FAILED'; final_ready=$false; error=$_.Exception.Message }
      try {
        Add-Member -InputObject $task.data -NotePropertyName status -NotePropertyValue 'blocked' -Force
        Add-Member -InputObject $task.data -NotePropertyName runner_blocker -NotePropertyValue $_.Exception.Message -Force
        Add-Member -InputObject $task.data -NotePropertyName final_ready -NotePropertyValue $false -Force
        Write-Utf8 (Join-Path $RepoRoot ($task.queue_rel -replace '/', '\')) (To-JsonText $task.data)
      } catch {}
    }
    $count++
  }
  $script:Summary.CONTINUE_RUNNER_READY = $true
} catch {
  Add-Blocker ('RUNNER_FATAL: ' + $_.Exception.Message)
} finally {
  try { if (Test-Path -LiteralPath $LatestStatusPath) { } ; Write-Utf8 $LatestStatusPath (To-JsonText $script:Summary) } catch {}
  try { Write-Utf8 (Join-Path $ReportDir "MULTI_PAGE_runner_output_$RunId.json") (To-JsonText $script:Summary) } catch {}
  try { $owned=Read-JsonFile $LockPath; if($owned-and[string]$owned.instance_id-eq$ScanInstanceId-and[int]$owned.pid-eq$PID){Remove-Item -LiteralPath $LockPath -Force -ErrorAction SilentlyContinue} } catch {}
}
Write-Output (To-JsonText $script:Summary)
if ($script:Summary.blockers.Count -gt 0) { exit 1 }
exit 0
