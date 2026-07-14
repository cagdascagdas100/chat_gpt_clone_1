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
$script:QueueGitRoot = $RepoRoot
$script:TaskGitRoot = $RepoRoot
$script:QueueGitRef = 'refs/remotes/origin/' + $MainBranch

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
function Add-GitPathsInBatches([string]$Root, [string[]]$Paths, [switch]$All) {
  $batch = [System.Collections.Generic.List[string]]::new()
  $batchChars = 0
  foreach ($path in @($Paths)) {
    $cost = ([string]$path).Length + 3
    if ($batch.Count -gt 0 -and ($batch.Count -ge 50 -or ($batchChars + $cost) -gt 6000)) {
      $args = @('add'); if ($All) { $args += '-A' }; $args += '--'; $args += @($batch)
      Assert-GitOk (Invoke-AaysGit -Cwd $Root -GitArgs $args) 'ADD_BATCH_FAILED'
      $batch.Clear(); $batchChars = 0
    }
    [void]$batch.Add([string]$path); $batchChars += $cost
  }
  if ($batch.Count -gt 0) {
    $args = @('add'); if ($All) { $args += '-A' }; $args += '--'; $args += @($batch)
    Assert-GitOk (Invoke-AaysGit -Cwd $Root -GitArgs $args) 'ADD_BATCH_FAILED'
  }
}
function Stage-AllowedOnly([string]$Root, [string[]]$Allowed) {
  # Stage only the contract paths. This avoids a full worktree scan on the
  # portable disk while still making it impossible to commit out-of-scope files.
  Add-GitPathsInBatches -Root $Root -Paths $Allowed -All
  $stagedResult = Invoke-AaysGit -Cwd $Root -GitArgs @('diff','--cached','--name-only','--diff-filter=ACMRD')
  Assert-GitOk $stagedResult 'STAGED_PATH_LIST_FAILED'
  $changed = @($stagedResult.output -split '\r?\n' | ForEach-Object { Rel $_ } | Where-Object { $_ })
  $unscoped = @($changed | Where-Object { -not (Path-IsAllowed $_ $Allowed) })
  if ($unscoped.Count -gt 0) { return [pscustomobject]@{ ok = $false; changed = $changed; unscoped = $unscoped } }
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
function Get-GitBlobSha([string]$Path) {
  $bytes = [System.IO.File]::ReadAllBytes($Path)
  $prefix = [System.Text.Encoding]::ASCII.GetBytes(('blob {0}' -f $bytes.Length) + [char]0)
  $sha = [System.Security.Cryptography.SHA1]::Create()
  try {
    [void]$sha.TransformBlock($prefix,0,$prefix.Length,$prefix,0)
    [void]$sha.TransformFinalBlock($bytes,0,$bytes.Length)
    return ([System.BitConverter]::ToString($sha.Hash)).Replace('-','').ToLowerInvariant()
  } finally {
    $sha.Dispose()
  }
}
function New-RemoteQueueMirror {
  $sourceRoot = $script:QueueGitRoot
  $remoteRef = $script:QueueGitRef
  $commitResult = Invoke-AaysGit $sourceRoot rev-parse $remoteRef
  Assert-GitOk $commitResult 'REMOTE_QUEUE_REF_MISSING'
  $remoteCommit = ([string]$commitResult.output).Trim()
  $listResult = Invoke-AaysGit $sourceRoot ls-tree -r $remoteRef -- 'docs/chatgpt_status'
  Assert-GitOk $listResult 'REMOTE_QUEUE_LIST_FAILED'
  $mirrorRoot = Join-Path $WorkRoot '_remote_queue_mirror'
  $tempRoot = Join-Path $WorkRoot ('_remote_queue_mirror_tmp_' + $PID)
  Assert-GeneratedQueueMirrorPath $mirrorRoot
  Assert-GeneratedQueueMirrorPath $tempRoot
  if (Test-Path -LiteralPath $tempRoot) { Remove-Item -LiteralPath $tempRoot -Recurse -Force }
  Ensure-Dir $tempRoot
  if (Test-Path -LiteralPath $mirrorRoot) {
    Get-ChildItem -LiteralPath $mirrorRoot -Force | ForEach-Object { Copy-Item -LiteralPath $_.FullName -Destination $tempRoot -Recurse -Force }
  }
  $queueEntries = @($listResult.output -split '\r?\n' | ForEach-Object {
    if ($_ -match '^[0-9]+\s+\w+\s+([0-9a-f]{40})\t(.+)$') {
      [pscustomobject]@{ sha=$Matches[1]; path=$Matches[2] }
    }
  } | Where-Object { $_.path -match '^docs/chatgpt_status/[^/]+/queue/[^/]+$' })
  $remotePaths = @{}
  $changedQueueCount = 0
  foreach ($entry in $queueEntries) {
    $queuePath = [string]$entry.path
    $remotePaths[$queuePath] = $true
    $destination = Join-Path $tempRoot ($queuePath -replace '/', '\\')
    if ((Test-Path -LiteralPath $destination) -and (Get-GitBlobSha $destination) -eq [string]$entry.sha) { continue }
    $showResult = Invoke-AaysGit $sourceRoot show ($remoteRef + ':' + $queuePath)
    Assert-GitOk $showResult ('REMOTE_QUEUE_READ_FAILED: ' + $queuePath)
    Ensure-Dir (Split-Path -Parent $destination)
    Write-Utf8 $destination ([string]$showResult.output)
    $changedQueueCount++
  }
  $tempDocs = Join-Path $tempRoot 'docs\chatgpt_status'
  if (Test-Path -LiteralPath $tempDocs) {
    Get-ChildItem -LiteralPath $tempDocs -Recurse -File -ErrorAction SilentlyContinue | Where-Object { $_.FullName -match '\\queue\\' } | ForEach-Object {
      $relative = Rel ($_.FullName.Substring($tempRoot.Length).TrimStart('\','/'))
      if (-not $remotePaths.ContainsKey($relative)) { Remove-Item -LiteralPath $_.FullName -Force }
    }
  }
  if (Test-Path -LiteralPath $mirrorRoot) { Remove-Item -LiteralPath $mirrorRoot -Recurse -Force }
  Move-Item -LiteralPath $tempRoot -Destination $mirrorRoot
  $script:RemoteQueueCommit = $remoteCommit
  $script:Summary.remote_queue_commit = $remoteCommit
  $script:Summary.remote_queue_count = $queueEntries.Count
  $script:Summary.remote_queue_changed_count = $changedQueueCount
  $script:Summary.queue_source = 'generated_remote_queue_mirror'
  return $mirrorRoot
}
function Sync-ControllerRepoSafe {
  if (-not (Test-Path -LiteralPath $RepoRoot)) { throw 'REPO_ROOT_MISSING: ' + $RepoRoot }
  Assert-GitOk (Invoke-AaysGit $RepoRoot config core.longpaths true) 'CONFIG_LONGPATHS_FAILED'
  $fetchArgs = @('-c','pack.windowMemory=8m','-c','pack.packSizeLimit=20m','-c','pack.threads=1','-c','core.compression=0','-c','fetch.negotiationAlgorithm=noop','-c','http.lowSpeedLimit=1','-c','http.lowSpeedTime=15','fetch','--no-tags','--depth=1','origin',("+refs/heads/${MainBranch}:refs/remotes/origin/${MainBranch}"))
  $fetchResult = $null
  $transportRoot = $null
  $worktreeContainer = Split-Path -Parent $RepoRoot
  $transport = Get-ChildItem -LiteralPath $worktreeContainer -Directory -Filter 'AAYS_RUNNER_PICKUP_FIX_PUBLISH_*' -ErrorAction SilentlyContinue |
    Where-Object { Test-Path -LiteralPath (Join-Path $_.FullName '.git') } |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1
  if ($transport) {
    $transportRoot = $transport.FullName
    $localProbe = Invoke-AaysGit -Cwd $transport.FullName -GitArgs @('rev-parse',("refs/heads/${MainBranch}"))
    $remoteProbe = Invoke-AaysGit -Cwd $transport.FullName -GitArgs @('ls-remote','--heads','origin',("refs/heads/${MainBranch}"))
    $localCommit = if($localProbe.code -eq 0){$localProbe.output.Trim()}else{''}
    $remoteCommit = if($remoteProbe.code -eq 0 -and $rem…8074 tokens truncated… Push-Sync $worktree $Task.target_branch "AAYS shared runner acknowledgement $page $taskId"
  $expectedClaimShaAfterAck = Get-GitBlobShaForFile $claimPath
  $currentPath = Join-Path $worktree ($currentRel -replace '/', '\')
  $expectedCurrentShaAfterAck = Get-GitBlobShaForFile $currentPath
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
  $automationTimedOut=$false
  $disableRunnerHeartbeat = As-Bool (Get-Prop $Task.data 'diagnostic_disable_runner_heartbeat')
  $maxRuntimeSeconds = $leaseSeconds
  $maxRuntimeRaw = Get-Prop $Task.data 'max_runtime_seconds'
  if ($null -ne $maxRuntimeRaw) { [void][int]::TryParse([string]$maxRuntimeRaw,[ref]$maxRuntimeSeconds) }
  $maxRuntimeSeconds = [math]::Max(5,$maxRuntimeSeconds)
  $stdoutPath = Join-Path ([IO.Path]::GetTempPath()) ("aays_${taskId}_$PID.stdout.log")
  $stderrPath = Join-Path ([IO.Path]::GetTempPath()) ("aays_${taskId}_$PID.stderr.log")
  try {
    Remove-Item -LiteralPath $stdoutPath,$stderrPath -Force -ErrorAction SilentlyContinue
    $child = Start-Process -FilePath (Join-Path $PSHOME 'powershell.exe') -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',('"' + $scriptPath + '"')) -WorkingDirectory $worktree -RedirectStandardOutput $stdoutPath -RedirectStandardError $stderrPath -PassThru -WindowStyle Hidden
    $automationStarted = [DateTimeOffset]::UtcNow
    $nextHeartbeat = $automationStarted.AddSeconds(5)
    while (-not $child.HasExited) {
      Start-Sleep -Seconds 2
      $child.Refresh()
      $now = [DateTimeOffset]::UtcNow
      if (-not $disableRunnerHeartbeat -and $now -ge $nextHeartbeat) {
        $runningPayload.last_heartbeat_at = $now.ToString('o')
        $runningPayload.lease_expires_at = $now.AddSeconds($leaseSeconds).ToString('o')
        $heartbeatClaim = Write-ClaimCas $claimPath (Get-GitBlobShaForFile $claimPath) $runningPayload
        if (-not $heartbeatClaim.ok) { throw 'CLAIM_HEARTBEAT_CAS_CONFLICT' }
        $expectedClaimShaAfterAck = $heartbeatClaim.actual_sha
        Write-TaskFile $worktree $heartbeatRel "TASK_ID=$taskId`nPAGE_KEY=$page`nCLAIM_ID=$claimId`nRUNNER_PID=$PID`nSTATUS=running`nHEARTBEAT_AT=$($runningPayload.last_heartbeat_at)`n"
        $nextHeartbeat = $now.AddSeconds(5)
      }
      $heartbeatExpired = $disableRunnerHeartbeat -and $now -ge [DateTimeOffset]::Parse([string]$runningPayload.lease_expires_at)
      $runtimeExpired = ($now - $automationStarted).TotalSeconds -ge $maxRuntimeSeconds
      if ($heartbeatExpired -or $runtimeExpired) {
        Stop-Process -Id $child.Id -Force -ErrorAction SilentlyContinue
        $automationTimedOut=$true
        break
      }
    }
    $child.WaitForExit()
    $child.Refresh()
    $automationCode = if ($automationTimedOut) { 124 } else { [int]$child.ExitCode }
    $stdout = if (Test-Path -LiteralPath $stdoutPath) { Get-Content -LiteralPath $stdoutPath -Raw } else { '' }
    $stderr = if (Test-Path -LiteralPath $stderrPath) { Get-Content -LiteralPath $stderrPath -Raw } else { '' }
    $automationOutput = ($stdout + $(if($stderr){"`n--- stderr ---`n$stderr"}else{''}))
  } catch {
    $automationCode=127
    $automationOutput=$_.Exception.Message
  } finally {
    Remove-Item -LiteralPath $stdoutPath,$stderrPath -Force -ErrorAction SilentlyContinue
    $env:AAYS_REPO_ROOT=$oldRoot; $env:AAYS_CONTROLLER_REPO_ROOT=$oldController; $env:AAYS_TASK_ID=$oldTask; $env:AAYS_PAGE_KEY=$oldPage; $env:AAYS_TARGET_BRANCH=$oldBranch; $env:PYTHONDONTWRITEBYTECODE=$oldNoBytecode
  }
  if ((Get-GitBlobShaForFile $currentPath) -ne $expectedCurrentShaAfterAck) {
    Assert-GitOk (Invoke-AaysGit $worktree checkout HEAD -- $currentRel) 'CURRENT_TASK_RESTORE_FAILED'
    Add-TaskBlocker $taskId $page 'DOMAIN_CURRENT_TASK_WRITE_BLOCKED'
    if ($automationCode -eq 0) { $automationCode=125 }
  }
  if ((Get-GitBlobShaForFile $claimPath) -ne $expectedClaimShaAfterAck) {
    Write-Utf8Atomic $claimPath (To-JsonText $runningPayload)
    Add-TaskBlocker $taskId $page 'DOMAIN_SHARED_CLAIM_WRITE_BLOCKED'
    if ($automationCode -eq 0) { $automationCode=125 }
  }
  if ($automationTimedOut) { Add-TaskBlocker $taskId $page 'CLAIM_HEARTBEAT_TIMEOUT_RECOVERY' }
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
    $terminalState = if ($automationTimedOut) { 'failed_recoverable' } else { 'blocked' }
    $terminalReason = if ($automationTimedOut) { 'CLAIM_HEARTBEAT_TIMEOUT_RECOVERY' } else { 'AUTOMATION_EXIT_NONZERO' }
    $terminalAt = Now-Utc
    $terminalClaim=[ordered]@{task_id=$taskId;page_key=$page;state=$terminalState;status=$terminalState;claim_id=$claimId;claimed_by='canonical-single-runner';claimed_at=$claimedAt;claim_source_sha=[string]$Task.claim_source_sha;lease_expires_at=[string]$runningPayload.lease_expires_at;runner_pid=$PID;last_heartbeat_at=[string]$runningPayload.last_heartbeat_at;terminal_at=$terminalAt;release_reason=$terminalReason;final_ready=$false}
    $terminalClaimWrite=Write-ClaimCas $claimPath (Get-GitBlobShaForFile $claimPath) $terminalClaim
    if(-not $terminalClaimWrite.ok){throw 'CLAIM_TERMINAL_CAS_CONFLICT'}
    $blockedPayload=[ordered]@{task_id=$taskId;page_key=$page;claim_id=$claimId;status=$terminalState;blocked_at=$terminalAt;automation_exit_code=$automationCode;runner_output_uploaded=$true;PUSH_SYNC_OK=$true;CONTINUE_RUNNER_READY=$true;blockers=@($terminalReason);final_ready=$false;product_final_ready=$false;fake_data=$false;db_write=$false;migration=$false;production_deploy=$false}
    Write-TaskFile $worktree $gateRel $blockedPayload
    Write-TaskFile $worktree $mirrorRel $blockedPayload
    Write-TaskFile $worktree $Task.queue_rel ([ordered]@{task_id=$taskId;page_key=$page;claim_id=$claimId;status=$terminalState;runner_blocked_at=$terminalAt;automation_exit_code=$automationCode;blockers=@($terminalReason);final_ready=$false;no_fake_final_ready=$true;no_db_write=$true;no_migration=$true;no_production_deploy=$true})
    Write-TaskFile $worktree $currentRel $terminalClaim
    Write-TaskFile $worktree $heartbeatRel "TASK_ID=$taskId`nPAGE_KEY=$page`nCLAIM_ID=$claimId`nSTATUS=$terminalState`nAUTOMATION_EXIT_CODE=$automationCode`nFINAL_READY=false`nHEARTBEAT_AT=$terminalAt`n"
    Write-StableRunnerGitHubHeartbeat $worktree $terminalState $page $taskId $claimId $false
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
  $finalReady = $false
  $completedAt=Now-Utc
  $doneClaim=[ordered]@{task_id=$taskId;page_key=$page;state='done';status='done';claim_id=$claimId;claimed_by='canonical-single-runner';claimed_at=$claimedAt;claim_source_sha=[string]$Task.claim_source_sha;lease_expires_at=[string]$runningPayload.lease_expires_at;runner_pid=$PID;last_heartbeat_at=[string]$runningPayload.last_heartbeat_at;terminal_at=$completedAt;release_reason='completed';final_ready=$false}
  $doneClaimWrite=Write-ClaimCas $claimPath (Get-GitBlobShaForFile $claimPath) $doneClaim
  if(-not $doneClaimWrite.ok){throw 'CLAIM_TERMINAL_CAS_CONFLICT'}
  $completed = [ordered]@{ task_id=$taskId; page_key=$page; claim_id=$claimId; completed_at=$completedAt; queue_seen=$true; queue_started=$true; single_runner_lock_acquired=$true; task_runs_in_clean_worktree=$true; allowed_paths_enforced=$true; runner_output_uploaded=$true; post_sync_ok=$true; PUSH_SYNC_OK=$true; CONTINUE_RUNNER_READY=$true; browser_environment=$browser; final_ready=$finalReady; fake_data=$false; db_write=$false; migration=$false; production_deploy=$false; blockers=@($script:Summary.blockers) }
  Write-TaskFile $worktree $completedRel $completed
  Write-TaskFile $worktree $mirrorRel $completed
  Write-TaskFile $worktree $Task.queue_rel ([ordered]@{ task_id=$taskId; page_key=$page; claim_id=$claimId; status='done'; runner_completed_at=$completedAt; PUSH_SYNC_OK=$true; CONTINUE_RUNNER_READY=$true; final_ready=$finalReady; no_fake_final_ready=$true; no_db_write=$true; no_migration=$true; no_production_deploy=$true })
  Write-TaskFile $worktree $currentRel $doneClaim
  Write-TaskFile $worktree $heartbeatRel "TASK_ID=$taskId`nPAGE_KEY=$page`nCLAIM_ID=$claimId`nSTATUS=completed`nPUSH_SYNC_OK=true`nCONTINUE_RUNNER_READY=true`nFINAL_READY=$finalReady`nHEARTBEAT_AT=$completedAt`n"
  Write-StableRunnerGitHubHeartbeat $worktree 'task_completed' $page $taskId $claimId $false
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
  # Lower numeric priority wins; equal priority is deterministic FIFO by created_at.
  $readyCandidates = @($parsed | Where-Object { $_.valid -and $_.task_id -ne 'aays1-f-portable-one-click-recovery-bootstrap-20260709' -and $_.status_norm -in @('queued','ready','pending','pending_repo_queue','pickup_requested','queued_for_single_shared_runner') } | Sort-Object priority, created_at, page_key, task_id)
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

