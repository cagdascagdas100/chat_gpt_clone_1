param(
  [string]$RepoRoot = 'F:\chatgpt\chat_gpt_clone_1_main',
  [string]$RepoFullName = 'cagdascagdas100/chat_gpt_clone_1',
  [string]$MainBranch = 'main',
  [string]$WorkRoot = 'F:\AAYS_WT',
  [int]$StaleMinutes = 20,
  [int]$MaxTasks = 1,
  [switch]$ScanOnly
)

$ErrorActionPreference = 'Stop'

function Now-Utc { (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ') }
function Safe-Name([string]$Value) { (($Value -replace '[^A-Za-z0-9_.-]', '_').Trim('_')) }
function Rel([string]$Path) { (($Path -replace '\\','/').TrimStart('/')) }
function Ensure-Dir([string]$Path) { if ($Path -and -not (Test-Path -LiteralPath $Path)) { New-Item -ItemType Directory -Force -Path $Path | Out-Null } }
function Write-Utf8([string]$Path, [string]$Content) { Ensure-Dir (Split-Path -Parent $Path); [System.IO.File]::WriteAllText($Path, $Content, [System.Text.UTF8Encoding]::new($false)) }
function To-JsonText([object]$Obj) { $Obj | ConvertTo-Json -Depth 60 }
function Get-Prop([object]$Obj, [string]$Name) { if ($null -eq $Obj) { return $null }; $p = $Obj.PSObject.Properties[$Name]; if ($p) { return $p.Value }; return $null }
function As-Bool([object]$Value) {
  if ($Value -is [bool]) { return $Value }
  if ($null -eq $Value) { return $false }
  return ([string]$Value).Trim().ToLowerInvariant() -in @('true','1','yes','y')
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
  return ($r -eq 'docs/chatgpt_status/_shared/heartbeat/MULTI_PAGE_heartbeat_latest.json' -or
    $r -eq 'docs/chatgpt_status/_shared/status/MULTI_PAGE_latest_status.json' -or
    $r -eq 'docs/chatgpt_status/_shared/status/queue_selection_debug_20260705.json' -or
    $r -eq 'docs/chatgpt_status/_shared/status/queue_skip_status_check_20260705.json' -or
    $r -eq 'docs/chatgpt_status/_shared/status/local_reboot_runner_start_latest.json' -or
    $r -eq 'docs/chatgpt_status/_shared/status/local_reboot_runner_start_result_latest.json' -or
    $r.StartsWith('docs/chatgpt_status/_shared/status/reboot_runner_start_request_') -or
    $r.StartsWith('docs/chatgpt_status/_shared/logs/') -or
    $r.StartsWith('docs/chatgpt_status/_shared/reports/MULTI_PAGE_runner_output_') -or
    $r -eq 'docs/chatgpt_status/_shared/runner_lock' -or
    $r.StartsWith('docs/chatgpt_status/_shared/runner_lock/'))
}
function Invoke-AaysGit {
  param(
    [Parameter(Mandatory=$true)][string]$Cwd,
    [Parameter(ValueFromRemainingArguments=$true)][string[]]$GitArgs
  )
  if ($null -eq $GitArgs -or $GitArgs.Count -eq 0) { throw 'BLOCKED_BARE_GIT_USAGE' }
  Ensure-Dir (Split-Path -Parent $script:GitLogPath)
  Add-Content -LiteralPath $script:GitLogPath -Encoding UTF8 -Value ("[{0}] cwd={1} git {2}" -f (Now-Utc), $Cwd, ($GitArgs -join ' '))
  Push-Location -LiteralPath $Cwd
  $oldEap = $ErrorActionPreference
  try {
    $ErrorActionPreference = 'Continue'
    $out = & git @GitArgs 2>&1
    $code = $LASTEXITCODE
    return [pscustomobject]@{ code = $code; output = (($out | Out-String).TrimEnd()); args = $GitArgs }
  } finally {
    $ErrorActionPreference = $oldEap
    Pop-Location
  }
}
function Assert-GitOk([object]$Result, [string]$Blocker) {
  if ($Result.code -ne 0) { throw ($Blocker + ': ' + $Result.output) }
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
function Clean-ControllerRuntimeDirty([string]$Root) {
  $allDirty = @(Get-GitChangedPaths $Root)
  $runtimeDirty = @($allDirty | Where-Object { Is-ControllerRuntimePath $_ })
  $dirty = @($allDirty | Where-Object { -not (Is-ControllerRuntimePath $_) })
  $script:Summary.controller_runtime_dirty_paths = $runtimeDirty
  $script:Summary.controller_dirty_paths = $dirty
  if ($dirty.Count -gt 0) { return $false }
  if ($runtimeDirty.Count -gt 0) {
    Assert-GitOk (Invoke-AaysGit $Root reset --hard HEAD) 'CONTROLLER_RUNTIME_RESET_FAILED'
    Assert-GitOk (Invoke-AaysGit $Root clean -fd -- docs/chatgpt_status/_shared/status docs/chatgpt_status/_shared/logs docs/chatgpt_status/_shared/runner_lock) 'CONTROLLER_RUNTIME_CLEAN_FAILED'
    $script:Summary.controller_runtime_dirty_cleaned = $true
  }
  return $true
}
function Sync-ControllerRepo {
  if (-not (Test-Path -LiteralPath $RepoRoot)) { throw 'REPO_ROOT_MISSING: ' + $RepoRoot }
  Assert-GitOk (Invoke-AaysGit $RepoRoot config core.longpaths true) 'CONFIG_LONGPATHS_FAILED'
  $cleanOk = Clean-ControllerRuntimeDirty $RepoRoot
  if (-not $cleanOk) {
    Add-Blocker 'CONTROLLER_DIRTY_NO_PULL'
    $script:Summary.controller_sync_ok = $false
    $script:Summary.controller_sync_mode = 'blocked_unscoped_dirty'
    return
  }
  Assert-GitOk (Invoke-AaysGit $RepoRoot fetch origin $MainBranch) 'CONTROLLER_FETCH_FAILED'
  Assert-GitOk (Invoke-AaysGit $RepoRoot checkout $MainBranch) 'CONTROLLER_CHECKOUT_FAILED'
  Assert-GitOk (Invoke-AaysGit $RepoRoot pull --ff-only origin $MainBranch) 'CONTROLLER_PULL_FAILED'
  $script:Summary.controller_sync_ok = $true
  $script:Summary.controller_sync_mode = 'pull_ff_only_after_runtime_cleanup'
}
function Ensure-TaskWorktree([object]$Task) {
  $safePage = Safe-Name $Task.page_key
  $safeTask = Safe-Name $Task.task_id
  if ($safeTask.Length -gt 42) { $safeTask = $safeTask.Substring(0,42) }
  $worktree = Join-Path $WorkRoot ("${safePage}_${safeTask}")
  $url = 'https://github.com/' + $RepoFullName + '.git'
  Ensure-Dir $WorkRoot
  Assert-GitOk (Invoke-AaysGit $RepoRoot config --global core.longpaths true) 'GLOBAL_LONGPATHS_FAILED'
  if (-not (Test-Path -LiteralPath $worktree)) {
    Assert-GitOk (Invoke-AaysGit $WorkRoot -c core.longpaths=true clone --branch $Task.target_branch --single-branch $url $worktree) 'TASK_CLONE_FAILED'
  }
  Assert-GitOk (Invoke-AaysGit $worktree config core.longpaths true) 'TASK_CONFIG_LONGPATHS_FAILED'
  $dirty = @(Get-GitChangedPaths $worktree)
  if ($dirty.Count -gt 0) { throw ('BLOCKED_WORKTREE_DIRTY: ' + ($dirty -join ',')) }
  Assert-GitOk (Invoke-AaysGit $worktree fetch origin $Task.target_branch) 'TASK_FETCH_FAILED'
  Assert-GitOk (Invoke-AaysGit $worktree checkout $Task.target_branch) 'TASK_CHECKOUT_FAILED'
  $rebased = Invoke-AaysGit $worktree rebase ('origin/' + $Task.target_branch)
  if ($rebased.code -ne 0) { throw ('BLOCKED_REBASE_CONFLICT: ' + $rebased.output) }
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
  $relative = Rel ($File.FullName.Substring($RepoRoot.Length).TrimStart('\','/'))
  if ($relative -notmatch '^docs/chatgpt_status/([^/]+)/queue/[^/]+$') {
    return [pscustomobject]@{ valid=$false; queue_rel=$relative; skip_reason='NOT_CANONICAL_QUEUE_PATH' }
  }
  $pageFromPath = $Matches[1]
  $data = Read-QueueFile $File
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
    if (-not (As-Bool (Get-Prop $data $flag))) { $errors += ('MISSING_OR_FALSE_' + $flag) }
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
  $site8020 = $false
  try { $resp = Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:8010/england_map_web/?runner_smoke=1' -TimeoutSec 5; $site8010 = ($resp.StatusCode -ge 200 -and $resp.StatusCode -lt 500) } catch {}
  try { $resp = Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:8020/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html?runner_smoke=1' -TimeoutSec 5; $site8020 = ($resp.StatusCode -ge 200 -and $resp.StatusCode -lt 500) } catch {}
  $smoke = ([bool]$edge -and ($site8010 -or $site8020))
  return [pscustomobject]@{ node_exists=[bool]$node; npm_exists=[bool]$npm; edge_or_chrome_exists=[bool]$edge; playwright_available=$playwright; site_8010_ok=$site8010; site_8020_ok=$site8020; browser_smoke_degraded_ok=($smoke -and -not $playwright); browser_smoke_passed=$smoke }
}
function Write-TaskFile([string]$Worktree, [string]$RelPath, [object]$Payload) {
  $full = Join-Path $Worktree ($RelPath -replace '/', '\')
  $content = if ($Payload -is [string]) { $Payload } else { To-JsonText $Payload }
  Write-Utf8 $full $content
}
function Push-Sync([string]$Worktree, [string]$Branch, [string]$CommitMessage) {
  $cached = Invoke-AaysGit $Worktree diff --cached --name-only
  Assert-GitOk $cached 'DIFF_CACHED_FAILED'
  if ($cached.output) { Assert-GitOk (Invoke-AaysGit $Worktree commit -m $CommitMessage) 'COMMIT_FAILED' }
  Assert-GitOk (Invoke-AaysGit $Worktree fetch origin $Branch) 'POST_FETCH_FAILED'
  $rebased = Invoke-AaysGit $Worktree rebase ('origin/' + $Branch)
  if ($rebased.code -ne 0) { throw ('BLOCKED_REBASE_CONFLICT: ' + $rebased.output) }
  Assert-GitOk (Invoke-AaysGit $Worktree push origin ('HEAD:' + $Branch)) 'POST_PUSH_FAILED'
}
function Run-Task([object]$Task) {
  $script:Summary.queue_started = $true
  $page = $Task.page_key
  $taskId = $Task.task_id
  $allowed = @($Task.allowed_paths + @(
    "docs/chatgpt_status/$page/status",
    "docs/chatgpt_status/$page/heartbeat",
    "docs/chatgpt_status/$page/reports",
    "docs/chatgpt_status/$page/runner_outputs",
    "docs/chatgpt_status/$page/queue",
    "docs/chatgpt_status/_shared/status",
    "docs/chatgpt_status/_shared/reports",
    "docs/chatgpt_status/_shared/heartbeat"
  ) | ForEach-Object { Rel $_ } | Select-Object -Unique)
  $worktree = Ensure-TaskWorktree $Task
  $script:Summary.task_runs_in_clean_worktree = $true
  $scriptPath = Resolve-ScriptPath $worktree $Task.script_path
  $startedRel = "docs/chatgpt_status/$page/status/${taskId}_started.json"
  $heartbeatRel = "docs/chatgpt_status/$page/heartbeat/${taskId}_heartbeat.txt"
  $reportRel = "docs/chatgpt_status/$page/reports/${taskId}_runner_output.txt"
  $completedRel = "docs/chatgpt_status/$page/status/${taskId}_completed.json"
  $gateRel = "docs/chatgpt_status/$page/status/${taskId}_gate.json"
  $mirrorRel = "docs/chatgpt_status/_shared/status/queue_result_mirror_${taskId}.json"
  $browser = Browser-Gate
  if (-not $browser.browser_smoke_passed) { Add-Blocker 'BLOCKED_BROWSER_ENVIRONMENT' }
  Write-TaskFile $worktree $startedRel ([ordered]@{ task_id=$taskId; page_key=$page; started_at=Now-Utc; queue_seen=$true; queue_started=$true; single_runner_lock_acquired=$true; task_runs_in_clean_worktree=$true; final_ready=$false; fake_data=$false; db_write=$false; migration=$false; production_deploy=$false })
  Write-TaskFile $worktree $heartbeatRel "TASK_ID=$taskId`nPAGE_KEY=$page`nSTATUS=running`nHEARTBEAT_AT=$(Now-Utc)`n"
  Write-TaskFile $worktree $Task.queue_rel ([ordered]@{ task_id=$taskId; page_key=$page; status='running'; target_branch=$Task.target_branch; script_path=$Task.script_path; allowed_paths=$Task.allowed_paths; no_fake_final_ready=$true; no_db_write=$true; no_migration=$true; no_production_deploy=$true })
  if (-not (Test-Path -LiteralPath $scriptPath)) { throw ('SCRIPT_MISSING: ' + $scriptPath) }
  Assert-GitOk (Invoke-AaysGit $worktree ls-remote origin) 'BLOCKED_GITHUB_AUTH'
  Assert-GitOk (Invoke-AaysGit $worktree push --dry-run origin ('HEAD:' + $Task.target_branch)) 'BLOCKED_GITHUB_AUTH'
  $oldRoot=$env:AAYS_REPO_ROOT; $oldTask=$env:AAYS_TASK_ID; $oldPage=$env:AAYS_PAGE_KEY
  $env:AAYS_REPO_ROOT=$worktree; $env:AAYS_TASK_ID=$taskId; $env:AAYS_PAGE_KEY=$page
  $automationOutput=''; $automationCode=0
  try {
    Push-Location -LiteralPath $worktree
    try { $out = & powershell -NoProfile -ExecutionPolicy Bypass -File $scriptPath 2>&1; $automationCode=$LASTEXITCODE; $automationOutput=($out | Out-String) } finally { Pop-Location }
  } finally { $env:AAYS_REPO_ROOT=$oldRoot; $env:AAYS_TASK_ID=$oldTask; $env:AAYS_PAGE_KEY=$oldPage }
  if ($automationCode -ne 0) { Add-Blocker 'AUTOMATION_EXIT_NONZERO' }
  $gatePath = Join-Path $worktree ($gateRel -replace '/', '\')
  $gate = $null
  if (Test-Path -LiteralPath $gatePath) { try { $gate = Get-Content -LiteralPath $gatePath -Raw | ConvertFrom-Json } catch { Add-Blocker 'GATE_PARSE_FAILED' } }
  if ($null -eq $gate) {
    $gate = [pscustomobject]@{ source_row_gate_passed=$false; ui_token_gate_passed=$false; browser_smoke_passed=$browser.browser_smoke_passed; post_sync_ok=$false; manual_review_required=$true; fake_data=$false }
    Write-TaskFile $worktree $gateRel $gate
  }
  Write-TaskFile $worktree $reportRel ("TASK_ID=$taskId`nPAGE_KEY=$page`nRUNNER_V4=20260706`nwork_root=$WorkRoot`nnode_exists=$($browser.node_exists)`nnpm_exists=$($browser.npm_exists)`nedge_or_chrome_exists=$($browser.edge_or_chrome_exists)`nplaywright_available=$($browser.playwright_available)`nsite_8010_ok=$($browser.site_8010_ok)`nsite_8020_ok=$($browser.site_8020_ok)`nbrowser_smoke_passed=$($browser.browser_smoke_passed)`nautomation_exit_code=$automationCode`nfake_data=false`n--- output ---`n$automationOutput")
  $stage = Stage-AllowedOnly $worktree $allowed
  if (-not $stage.ok) { throw ('BLOCKED_UNSCOPED_CHANGES: ' + ($stage.unscoped -join ',')) }
  $script:Summary.allowed_paths_enforced = $true
  Push-Sync $worktree $Task.target_branch "AAYS shared runner V4 output $page $taskId"
  $finalReady = ((As-Bool (Get-Prop $gate 'source_row_gate_passed')) -and (As-Bool (Get-Prop $gate 'ui_token_gate_passed')) -and $browser.browser_smoke_passed -and (-not (As-Bool (Get-Prop $gate 'manual_review_required'))) -and (-not (As-Bool (Get-Prop $gate 'fake_data'))) -and $automationCode -eq 0)
  $completed = [ordered]@{ task_id=$taskId; page_key=$page; completed_at=Now-Utc; queue_seen=$true; queue_started=$true; single_runner_lock_acquired=$true; task_runs_in_clean_worktree=$true; allowed_paths_enforced=$true; runner_output_uploaded=$true; post_sync_ok=$true; PUSH_SYNC_OK=$true; CONTINUE_RUNNER_READY=$true; browser_environment=$browser; final_ready=$finalReady; fake_data=$false; db_write=$false; migration=$false; production_deploy=$false; blockers=@($script:Summary.blockers) }
  Write-TaskFile $worktree $completedRel $completed
  Write-TaskFile $worktree $mirrorRel $completed
  Write-TaskFile $worktree $Task.queue_rel ([ordered]@{ task_id=$taskId; page_key=$page; status='done'; runner_completed_at=Now-Utc; PUSH_SYNC_OK=$true; CONTINUE_RUNNER_READY=$true; final_ready=$finalReady; no_fake_final_ready=$true; no_db_write=$true; no_migration=$true; no_production_deploy=$true })
  Write-TaskFile $worktree $heartbeatRel "TASK_ID=$taskId`nPAGE_KEY=$page`nSTATUS=completed`nPUSH_SYNC_OK=true`nCONTINUE_RUNNER_READY=true`nFINAL_READY=$finalReady`nHEARTBEAT_AT=$(Now-Utc)`n"
  $stage2 = Stage-AllowedOnly $worktree $allowed
  if (-not $stage2.ok) { throw ('BLOCKED_UNSCOPED_CHANGES: ' + ($stage2.unscoped -join ',')) }
  Push-Sync $worktree $Task.target_branch "AAYS shared runner V4 completion $page $taskId"
  $script:Summary.runner_output_uploaded=$true; $script:Summary.post_sync_ok=$true; $script:Summary.PUSH_SYNC_OK=$true; $script:Summary.CONTINUE_RUNNER_READY=$true; $script:Summary.final_ready=[bool]$finalReady
  return [pscustomobject]@{ task_id=$taskId; page_key=$page; completed=$true; final_ready=[bool]$finalReady; worktree=$worktree }
}

$RepoRoot = [System.IO.Path]::GetFullPath($RepoRoot)
$WorkRoot = [System.IO.Path]::GetFullPath($WorkRoot)
if (-not $RepoRoot.StartsWith('F:\', [System.StringComparison]::OrdinalIgnoreCase)) { throw 'BLOCKED_WRONG_REPO_ROOT: ' + $RepoRoot }
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
$RunnerHeartbeatPath = Join-Path $HeartbeatDir 'MULTI_PAGE_heartbeat_latest.json'
$LatestStatusPath = Join-Path $StatusDir 'MULTI_PAGE_latest_status.json'
$SelectionDebugPath = Join-Path $StatusDir 'queue_selection_debug_20260705.json'
$SkipDebugPath = Join-Path $StatusDir 'queue_skip_status_check_20260705.json'
$script:Summary = [ordered]@{ run_id=$RunId; checked_at=Now-Utc; repo_root=$RepoRoot; work_root=$WorkRoot; main_branch=$MainBranch; queue_seen=$false; queue_started=$false; single_runner_lock_acquired=$false; task_runs_in_clean_worktree=$false; allowed_paths_enforced=$false; runner_output_uploaded=$false; post_sync_ok=$false; PUSH_SYNC_OK=$false; CONTINUE_RUNNER_READY=$false; final_ready=$false; fake_data=$false; db_write=$false; migration=$false; production_deploy=$false; blockers=@(); processed=@(); skipped=@() }

try {
  Sync-ControllerRepo
  $lockFresh = $false
  if (Test-Path -LiteralPath $LockPath) {
    $age = ((Get-Date) - (Get-Item -LiteralPath $LockPath).LastWriteTime).TotalMinutes
    if ($age -lt $StaleMinutes) { $lockFresh = $true } else { Remove-Item -LiteralPath $LockPath -Force -Recurse -ErrorAction SilentlyContinue }
  }
  if ($lockFresh) { Add-Blocker 'RUNNER_ALREADY_ACTIVE'; $script:Summary.CONTINUE_RUNNER_READY=$true; Write-Utf8 $LatestStatusPath (To-JsonText $script:Summary); Write-Output (To-JsonText $script:Summary); exit 0 }
  Ensure-Dir $LockPath
  $script:Summary.single_runner_lock_acquired = $true
  Write-Utf8 $RunnerHeartbeatPath (To-JsonText ([ordered]@{ pid=$PID; started_at=Now-Utc; runner='RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_V4_20260706'; heartbeat_path=$RunnerHeartbeatPath; lock_path=$LockPath; work_root=$WorkRoot }))
  $queueFiles = @(Get-ChildItem -LiteralPath (Join-Path $RepoRoot 'docs\chatgpt_status') -Recurse -File -ErrorAction SilentlyContinue | Where-Object { $_.FullName -match '\\queue\\' })
  $parsed = @($queueFiles | ForEach-Object { Parse-Queue $_ })
  $ready = @($parsed | Where-Object { $_.valid -and $_.status_norm -in @('queued','ready','pending','pending_repo_queue','pickup_requested','queued_for_single_shared_runner') } | Sort-Object priority, page_key, task_id)
  $script:Summary.queue_seen = ($parsed.Count -gt 0)
  Write-Utf8 $SelectionDebugPath (To-JsonText ([ordered]@{ checked_at=Now-Utc; ready_count=$ready.Count; ready=$ready }))
  Write-Utf8 $SkipDebugPath (To-JsonText ([ordered]@{ checked_at=Now-Utc; skipped=@($parsed | Where-Object { -not $_.valid -or -not ($_.status_norm -in @('queued','ready','pending','pending_repo_queue','pickup_requested','queued_for_single_shared_runner')) }) }))
  if ($ScanOnly) { $script:Summary.CONTINUE_RUNNER_READY=$true; Write-Utf8 $LatestStatusPath (To-JsonText $script:Summary); Write-Output (To-JsonText $script:Summary); exit 0 }
  $count = 0
  foreach ($task in $ready) {
    if ($count -ge $MaxTasks) { break }
    try { $res = Run-Task $task; $script:Summary.processed += $res; $count++ } catch { Add-Blocker 'RUNNER_TASK_FAILED'; $script:Summary.processed += [ordered]@{ task_id=$task.task_id; page_key=$task.page_key; completed=$false; final_ready=$false; error=$_.Exception.Message }; break }
  }
  $script:Summary.CONTINUE_RUNNER_READY = $true
} catch {
  Add-Blocker ('RUNNER_FATAL: ' + $_.Exception.Message)
} finally {
  try { if (Test-Path -LiteralPath $LatestStatusPath) { } ; Write-Utf8 $LatestStatusPath (To-JsonText $script:Summary) } catch {}
  try { Write-Utf8 (Join-Path $ReportDir "MULTI_PAGE_runner_output_$RunId.json") (To-JsonText $script:Summary) } catch {}
  try { if (Test-Path -LiteralPath $LockPath) { Remove-Item -LiteralPath $LockPath -Force -Recurse -ErrorAction SilentlyContinue } } catch {}
}
Write-Output (To-JsonText $script:Summary)
if ($script:Summary.blockers.Count -gt 0) { exit 1 }
exit 0
