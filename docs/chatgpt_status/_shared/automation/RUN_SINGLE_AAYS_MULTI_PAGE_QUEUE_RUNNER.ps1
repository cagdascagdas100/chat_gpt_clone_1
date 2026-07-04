param(
  [string]$RepoRoot = 'F:\chatgpt\chat_gpt_clone_1_main',
  [string]$RepoFullName = 'cagdascagdas100/chat_gpt_clone_1',
  [string]$MainBranch = 'main',
  [int]$StaleMinutes = 20,
  [int]$MaxTasks = 1
)

$ErrorActionPreference = 'Stop'
$script:GitLogPath = $null
$script:RunSummary = [ordered]@{
  queue_seen = $false
  queue_started = $false
  single_runner_lock_acquired = $false
  task_runs_in_clean_worktree = $false
  allowed_paths_enforced = $false
  runner_output_uploaded = $false
  post_sync_ok = $false
  PUSH_SYNC_OK = $false
  CONTINUE_RUNNER_READY = $false
  final_ready = $false
  blockers = @()
}

function Full-Path([string]$Path) { return [System.IO.Path]::GetFullPath($Path) }
function Normalize-Rel([string]$Path) { return (($Path -replace '\\','/').TrimStart('/')) }
function Safe-Name([string]$Value) { return (($Value -replace '[^A-Za-z0-9_.-]','_').Trim('_')) }
function Now-Utc() { return (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ') }
function Ensure-Dir([string]$Path) { if ($Path -and -not (Test-Path -LiteralPath $Path)) { New-Item -ItemType Directory -Force -Path $Path | Out-Null } }
function Write-Utf8([string]$Path, [string]$Content) {
  Ensure-Dir (Split-Path -Parent $Path)
  [System.IO.File]::WriteAllText($Path, $Content, [System.Text.UTF8Encoding]::new($false))
}
function Json([object]$Obj) { return ($Obj | ConvertTo-Json -Depth 24) }
function Add-Blocker([string]$Code) {
  if (-not ($script:RunSummary.blockers -contains $Code)) { $script:RunSummary.blockers += $Code }
}

function Invoke-AaysGit {
  param([Parameter(ValueFromRemainingArguments=$true)][string[]]$GitArgs)
  if (-not $GitArgs -or $GitArgs.Count -eq 0) { throw 'BLOCKED_BARE_GIT_USAGE: Invoke-AaysGit requires explicit arguments.' }
  $line = (Now-Utc) + ' git ' + ($GitArgs -join ' ')
  if ($script:GitLogPath) { Add-Content -LiteralPath $script:GitLogPath -Value $line -Encoding UTF8 }
  $oldEap = $ErrorActionPreference
  $ErrorActionPreference = 'Continue'
  try {
    $out = & git @GitArgs 2>&1
  } finally {
    $ErrorActionPreference = $oldEap
  }
  $code = $LASTEXITCODE
  if ($script:GitLogPath -and $out) { Add-Content -LiteralPath $script:GitLogPath -Value (($out | Out-String).TrimEnd()) -Encoding UTF8 }
  [pscustomobject]@{ code = $code; output = (($out | Out-String).TrimEnd()); args = @($GitArgs) }
}

function Assert-GitOk([object]$Result, [string]$Blocker) {
  if ($Result.code -ne 0) { throw ($Blocker + ': ' + $Result.output) }
}

function Read-QueueFile([System.IO.FileInfo]$File) {
  $raw = Get-Content -LiteralPath $File.FullName -Raw -ErrorAction Stop
  if ($File.Extension -ieq '.json') {
    $obj = $raw | ConvertFrom-Json
    return [pscustomobject]@{ raw = $raw; data = $obj; parse_ok = $true; parse_error = $null }
  }
  $map = [ordered]@{}
  foreach ($line in ($raw -split "`r?`n")) {
    $trim = $line.Trim()
    if (-not $trim -or $trim.StartsWith('#') -or $trim -notmatch '=') { continue }
    $idx = $trim.IndexOf('=')
    $key = $trim.Substring(0,$idx).Trim()
    $val = $trim.Substring($idx+1).Trim()
    $map[$key] = $val
  }
  return [pscustomobject]@{ raw = $raw; data = [pscustomobject]$map; parse_ok = $true; parse_error = $null }
}

function Get-Prop([object]$Obj, [string]$Name) {
  if ($null -eq $Obj) { return $null }
  $p = $Obj.PSObject.Properties[$Name]
  if ($p) { return $p.Value }
  return $null
}

function As-Bool([object]$Value) {
  if ($Value -is [bool]) { return $Value }
  if ($null -eq $Value) { return $false }
  return ([string]$Value).Trim().ToLowerInvariant() -in @('true','1','yes','y')
}

function As-PathList([object]$Value) {
  if ($null -eq $Value) { return @() }
  if ($Value -is [System.Array]) { return @($Value | ForEach-Object { Normalize-Rel ([string]$_) } | Where-Object { $_ }) }
  return @(([string]$Value -split '[,;]' | ForEach-Object { Normalize-Rel $_ } | Where-Object { $_ }))
}

function Validate-Queue([System.IO.FileInfo]$QueueFile, [object]$Data) {
  $blockers = New-Object System.Collections.Generic.List[string]
  $pageKey = [string](Get-Prop $Data 'page_key')
  $scriptPath = [string](Get-Prop $Data 'script_path')
  $targetBranch = [string](Get-Prop $Data 'target_branch')
  $taskId = [string](Get-Prop $Data 'task_id')
  if (-not $taskId) { $taskId = [System.IO.Path]::GetFileNameWithoutExtension($QueueFile.Name) }
  $status = [string](Get-Prop $Data 'status')
  if (-not $status) { $status = 'queued' }
  $allowedPaths = As-PathList (Get-Prop $Data 'allowed_paths')

  if (-not $pageKey) { $blockers.Add('MISSING_page_key') }
  if (-not $scriptPath) { $blockers.Add('MISSING_script_path') }
  if (-not $targetBranch) { $blockers.Add('MISSING_target_branch') }
  if ($allowedPaths.Count -eq 0) { $blockers.Add('MISSING_allowed_paths') }
  foreach ($flag in @('no_fake_final_ready','no_db_write','no_migration','no_production_deploy')) {
    if (-not (As-Bool (Get-Prop $Data $flag))) { $blockers.Add('MISSING_OR_FALSE_' + $flag) }
  }
  if ($pageKey) {
    $expectedRoot = Normalize-Rel "docs/chatgpt_status/$pageKey/queue"
    $actual = Normalize-Rel ($QueueFile.FullName.Substring($RepoRoot.Length).TrimStart('\','/'))
    if (-not $actual.StartsWith($expectedRoot + '/')) { $blockers.Add('PAGE_KEY_PATH_MISMATCH') }
  }

  [pscustomobject]@{
    queue_file = $QueueFile.FullName
    queue_rel = Normalize-Rel ($QueueFile.FullName.Substring($RepoRoot.Length).TrimStart('\','/'))
    valid = ($blockers.Count -eq 0)
    blockers = @($blockers)
    page_key = $pageKey
    task_id = (Safe-Name $taskId)
    script_path = $scriptPath
    target_branch = $targetBranch
    allowed_paths = @($allowedPaths)
    status = $status
    data = $Data
  }
}

function Write-SharedStatus([string]$Name, [object]$Payload) {
  $path = Join-Path $SharedStatusDir $Name
  Write-Utf8 $path (Json $Payload)
}

function Write-SharedReport([string]$Name, [object]$Payload) {
  $path = Join-Path $SharedReportsDir $Name
  Write-Utf8 $path (Json $Payload)
}

function Test-BrowserEnvironment() {
  $node = Get-Command node -ErrorAction SilentlyContinue
  $npm = Get-Command npm -ErrorAction SilentlyContinue
  $edgeCandidates = @(
    "$env:ProgramFiles (x86)\Microsoft\Edge\Application\msedge.exe",
    "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe",
    "$env:LOCALAPPDATA\Microsoft\Edge\Application\msedge.exe"
  )
  $edge = $edgeCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
  $playwrightOk = $false
  $playwrightError = $null
  if ($node) {
    $oldEap = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
      $out = & node -e "try{require.resolve('playwright');process.exit(0)}catch(e){console.error(e.message);process.exit(2)}" 2>&1
    } finally {
      $ErrorActionPreference = $oldEap
    }
    $playwrightOk = ($LASTEXITCODE -eq 0)
    if (-not $playwrightOk) { $playwrightError = ($out | Out-String).Trim() }
  }
  $siteOk = $false
  $siteStatus = $null
  $siteError = $null
  try {
    $r = Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:8020/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html?refresh=shared-runner' -TimeoutSec 5
    $siteStatus = [int]$r.StatusCode
    $siteOk = ($siteStatus -ge 200 -and $siteStatus -lt 400)
  } catch { $siteError = $_.Exception.Message }
  [pscustomobject]@{
    node_exists = [bool]$node
    npm_exists = [bool]$npm
    edge_exists = [bool]$edge
    edge_path = $edge
    playwright_exists = $playwrightOk
    playwright_error = $playwrightError
    site_8020_ok = $siteOk
    site_8020_status = $siteStatus
    site_8020_error = $siteError
    browser_smoke_passed = ([bool]$node -and [bool]$npm -and [bool]$edge -and $playwrightOk -and $siteOk)
  }
}

function Get-FinalReadyFromGate([object]$Gate) {
  if ($null -eq $Gate) { return $false }
  $source = As-Bool (Get-Prop $Gate 'source_row_gate_passed')
  $ui = As-Bool (Get-Prop $Gate 'ui_token_gate_passed')
  $browser = As-Bool (Get-Prop $Gate 'browser_smoke_passed')
  $sync = As-Bool (Get-Prop $Gate 'post_sync_ok')
  $manualReview = As-Bool (Get-Prop $Gate 'manual_review_required')
  $fake = As-Bool (Get-Prop $Gate 'fake_data')
  return ($source -and $ui -and $browser -and $sync -and -not $manualReview -and -not $fake)
}

function Resolve-ScriptPath([string]$Worktree, [string]$ScriptPath) {
  if (-not $ScriptPath) { return $null }
  $candidate = $ScriptPath
  if ([System.IO.Path]::IsPathRooted($candidate)) {
    if (Test-Path -LiteralPath $candidate) { return $candidate }
    $m = [regex]::Match($candidate, 'docs[\\/]chatgpt_status[\\/].+$')
    if ($m.Success) { return Join-Path $Worktree ($m.Value -replace '/', '\') }
    return $candidate
  }
  return Join-Path $Worktree ($candidate -replace '/', '\')
}

function Get-ChangedRelPaths([string]$Worktree) {
  Push-Location -LiteralPath $Worktree
  try {
    $statusResult = Invoke-AaysGit status --porcelain
    Assert-GitOk $statusResult 'BLOCKED_GIT_STATUS_FAILED'
    $lines = @($statusResult.output -split '\r?\n' | Where-Object { $_ })
    $paths = @()
    foreach ($line in $lines) {
      if ($line.Length -lt 4) { continue }
      $p = $line.Substring(3).Trim()
      if ($p -match ' -> ') { $p = ($p -split ' -> ')[-1] }
      $paths += (Normalize-Rel $p.Trim('"'))
    }
    return @($paths | Where-Object { $_ })
  } finally { Pop-Location }
}

function Is-AllowedPath([string]$Path, [string[]]$Allowed) {
  $p = Normalize-Rel $Path
  foreach ($a in $Allowed) {
    $aa = Normalize-Rel $a
    if (-not $aa) { continue }
    if ($p -eq $aa -or $p.StartsWith($aa.TrimEnd('/') + '/')) { return $true }
  }
  return $false
}

function Write-TaskFile([string]$Worktree, [string]$Rel, [string]$Content) {
  Write-Utf8 (Join-Path $Worktree ($Rel -replace '/', '\')) $Content
}

function Stage-AllowedChanges([string]$Worktree, [string[]]$AllowedPaths) {
  $changed = Get-ChangedRelPaths $Worktree
  $unscoped = @($changed | Where-Object { -not (Is-AllowedPath $_ $AllowedPaths) })
  if ($unscoped.Count -gt 0) {
    return [pscustomobject]@{ ok = $false; changed = $changed; unscoped = $unscoped }
  }
  Push-Location -LiteralPath $Worktree
  try {
    foreach ($p in $changed) { if ($p) { $r = Invoke-AaysGit add -- $p; Assert-GitOk $r 'BLOCKED_GIT_ADD_FAILED' } }
  } finally { Pop-Location }
  [pscustomobject]@{ ok = $true; changed = $changed; unscoped = @() }
}

function Prepare-CleanWorktree([object]$Task) {
  $base = 'C:\Users\cagda\Documents\GitHub'
  $name = 'AAYS_' + (Safe-Name $Task.page_key) + '_' + (Safe-Name $Task.task_id)
  if ($name.Length -gt 120) { $name = $name.Substring(0,120) }
  $worktree = Join-Path $base $name
  $repoUrl = 'https://github.com/' + $RepoFullName + '.git'
  if (-not (Test-Path -LiteralPath $worktree)) {
    Ensure-Dir $base
    $clone = Invoke-AaysGit clone --branch $Task.target_branch --single-branch $repoUrl $worktree
    Assert-GitOk $clone 'BLOCKED_WORKTREE_CLONE_FAILED'
  }
  if (-not (Test-Path -LiteralPath (Join-Path $worktree '.git'))) { throw 'BLOCKED_WORKTREE_NOT_GIT: ' + $worktree }
  Push-Location -LiteralPath $worktree
  try {
    $dirtyResult = Invoke-AaysGit status --porcelain
    Assert-GitOk $dirtyResult 'BLOCKED_WORKTREE_STATUS_FAILED'
    $dirty = ($dirtyResult.output | Out-String).Trim()
    if ($dirty) { throw 'BLOCKED_WORKTREE_DIRTY: ' + $worktree }
    $fetch = Invoke-AaysGit fetch origin $Task.target_branch
    Assert-GitOk $fetch 'BLOCKED_TARGET_FETCH_FAILED'
    $checkout = Invoke-AaysGit checkout $Task.target_branch
    if ($checkout.code -ne 0) { $checkout = Invoke-AaysGit checkout -B $Task.target_branch ('origin/' + $Task.target_branch) }
    Assert-GitOk $checkout 'BLOCKED_TARGET_CHECKOUT_FAILED'
    $rebase = Invoke-AaysGit rebase ('origin/' + $Task.target_branch)
    if ($rebase.code -ne 0) { throw 'BLOCKED_REBASE_CONFLICT: ' + $rebase.output }
  } finally { Pop-Location }
  return $worktree
}

function Process-QueueTask([object]$Task) {
  $script:RunSummary.queue_started = $true
  $page = $Task.page_key
  $taskId = $Task.task_id
  $systemAllowed = @(
    "docs/chatgpt_status/$page/status/",
    "docs/chatgpt_status/$page/heartbeat/",
    "docs/chatgpt_status/$page/reports/",
    "docs/chatgpt_status/$page/runner_outputs/",
    "docs/chatgpt_status/$page/queue/"
  )
  $allowed = @($Task.allowed_paths + $systemAllowed | ForEach-Object { Normalize-Rel $_ } | Select-Object -Unique)
  $browserGate = Test-BrowserEnvironment
  if (-not $browserGate.browser_smoke_passed) { Add-Blocker 'BLOCKED_BROWSER_ENVIRONMENT' }

  $worktree = Prepare-CleanWorktree $Task
  $script:RunSummary.task_runs_in_clean_worktree = $true
  $scriptPath = Resolve-ScriptPath $worktree $Task.script_path
  if (-not (Test-Path -LiteralPath $scriptPath)) { throw 'BLOCKED_MISSING_SCRIPT_PATH: ' + $scriptPath }

  $scriptText = Get-Content -LiteralPath $scriptPath -Raw -ErrorAction SilentlyContinue
  if ($scriptText -match '(?i)(git\s+reset\s+--hard|git\s+push\s+--force|--force-with-lease|production_deploy\s*=\s*true|migration\s*=\s*true|db_write\s*=\s*true)') {
    throw 'BLOCKED_FORBIDDEN_SCRIPT_TOKEN: script contains reset/force/db/migration/deploy token.'
  }

  $startedRel = "docs/chatgpt_status/$page/status/${taskId}_started.json"
  $heartbeatRel = "docs/chatgpt_status/$page/heartbeat/${taskId}_heartbeat.txt"
  $reportRel = "docs/chatgpt_status/$page/reports/${taskId}_runner_output.txt"
  $completedRel = "docs/chatgpt_status/$page/status/${taskId}_completed.json"
  $gateRel = "docs/chatgpt_status/$page/status/${taskId}_gate.json"

  $startedPayload = [ordered]@{
    task_id = $taskId
    page_key = $page
    queue_file = $Task.queue_rel
    queue_seen = $true
    queue_started = $true
    single_runner_lock_acquired = $true
    task_runs_in_clean_worktree = $true
    allowed_paths = $allowed
    started_at = Now-Utc
    final_ready = $false
    fake_data = $false
  }
  Write-TaskFile $worktree $startedRel (Json $startedPayload)
  $queueRunning = [ordered]@{
    task_id = $taskId
    page_key = $page
    status = 'running'
    runner_started_at = Now-Utc
    original_queue_file = $Task.queue_rel
    script_path = $Task.script_path
    target_branch = $Task.target_branch
    allowed_paths = $Task.allowed_paths
    no_fake_final_ready = $true
    no_db_write = $true
    no_migration = $true
    no_production_deploy = $true
  }
  Write-TaskFile $worktree $Task.queue_rel (Json $queueRunning)
  Write-TaskFile $worktree $heartbeatRel ("TASK_ID=$taskId`nPAGE_KEY=$page`nRUNNER_TOUCHED=true`nHEARTBEAT_AT=$(Now-Utc)`nSTATUS=running`n")

  $auth1 = Invoke-AaysGit -C $worktree ls-remote origin
  if ($auth1.code -ne 0) { throw 'BLOCKED_GITHUB_AUTH: ls-remote failed: ' + $auth1.output }
  $auth2 = Invoke-AaysGit -C $worktree push --dry-run origin ('HEAD:' + $Task.target_branch)
  if ($auth2.code -ne 0) { throw 'BLOCKED_GITHUB_AUTH: push dry-run failed: ' + $auth2.output }

  $oldRepoRoot = $env:AAYS_REPO_ROOT
  $oldPageKey = $env:AAYS_PAGE_KEY
  $oldTaskId = $env:AAYS_TASK_ID
  $env:AAYS_REPO_ROOT = $worktree
  $env:AAYS_PAGE_KEY = $page
  $env:AAYS_TASK_ID = $taskId
  $out = $null
  $exitCode = 0
  try {
    Push-Location -LiteralPath $worktree
    try {
      $out = & powershell -NoProfile -ExecutionPolicy Bypass -File $scriptPath 2>&1
      $exitCode = $LASTEXITCODE
    } finally { Pop-Location }
  } finally {
    $env:AAYS_REPO_ROOT = $oldRepoRoot
    $env:AAYS_PAGE_KEY = $oldPageKey
    $env:AAYS_TASK_ID = $oldTaskId
  }
  if ($exitCode -ne 0) { Add-Blocker 'AUTOMATION_EXIT_NONZERO' }

  $gate = $null
  $gatePath = Join-Path $worktree ($gateRel -replace '/', '\')
  if (Test-Path -LiteralPath $gatePath) {
    try { $gate = Get-Content -LiteralPath $gatePath -Raw | ConvertFrom-Json } catch { Add-Blocker 'GATE_JSON_PARSE_FAILED' }
  }
  if (-not $gate) {
    $gate = [pscustomobject]@{
      source_row_gate_passed = $false
      ui_token_gate_passed = $false
      browser_smoke_passed = [bool]$browserGate.browser_smoke_passed
      post_sync_ok = $false
      manual_review_required = $true
      fake_data = $false
    }
    Write-TaskFile $worktree $gateRel (Json $gate)
  }

  $report = @"
AAYS Single Shared Runner Output
TASK_ID=$taskId
PAGE_KEY=$page
TARGET_BRANCH=$($Task.target_branch)
QUEUE_FILE=$($Task.queue_rel)
SCRIPT_PATH=$scriptPath
CLEAN_WORKTREE=$worktree
single_runner_lock_acquired=true
task_runs_in_clean_worktree=true
browser_smoke_passed=$($browserGate.browser_smoke_passed)
automation_exit_code=$exitCode
fake_data=$false
no_db_write=true
no_migration=true
no_production_deploy=true

--- automation output ---
$($out | Out-String)
"@
  Write-TaskFile $worktree $reportRel $report

  $stage1 = Stage-AllowedChanges $worktree $allowed
  if (-not $stage1.ok) {
    $blocker = [ordered]@{ task_id=$taskId; blocker='BLOCKED_UNSCOPED_CHANGES'; unscoped_changes=$stage1.unscoped; changed=$stage1.changed; allowed_paths=$allowed; final_ready=$false }
    Write-TaskFile $worktree $reportRel ((Json $blocker) + "`n")
    throw 'BLOCKED_UNSCOPED_CHANGES: ' + ([string]::Join(',', $stage1.unscoped))
  }
  $script:RunSummary.allowed_paths_enforced = $true

  Push-Location -LiteralPath $worktree
  try {
    $cachedResult = Invoke-AaysGit diff --cached --name-only
    Assert-GitOk $cachedResult 'BLOCKED_GIT_DIFF_FAILED'
    $cached = ($cachedResult.output | Out-String).Trim()
    if ($cached) {
      $commit = Invoke-AaysGit commit -m ("AAYS shared runner output " + $page + " " + $taskId)
      Assert-GitOk $commit 'BLOCKED_COMMIT_FAILED'
    }
    $fetch = Invoke-AaysGit fetch origin $Task.target_branch
    Assert-GitOk $fetch 'BLOCKED_POST_FETCH_FAILED'
    $rebase = Invoke-AaysGit rebase ('origin/' + $Task.target_branch)
    if ($rebase.code -ne 0) { throw 'BLOCKED_REBASE_CONFLICT: ' + $rebase.output }
    $push = Invoke-AaysGit push origin ('HEAD:' + $Task.target_branch)
    Assert-GitOk $push 'BLOCKED_PUSH_FAILED'
  } finally { Pop-Location }
  $script:RunSummary.runner_output_uploaded = $true
  $script:RunSummary.post_sync_ok = $true
  $script:RunSummary.PUSH_SYNC_OK = $true

  $finalGate = [pscustomobject]@{
    source_row_gate_passed = As-Bool (Get-Prop $gate 'source_row_gate_passed')
    ui_token_gate_passed = As-Bool (Get-Prop $gate 'ui_token_gate_passed')
    browser_smoke_passed = [bool]$browserGate.browser_smoke_passed
    post_sync_ok = $true
    manual_review_required = As-Bool (Get-Prop $gate 'manual_review_required')
    fake_data = As-Bool (Get-Prop $gate 'fake_data')
  }
  $finalReady = Get-FinalReadyFromGate $finalGate
  $script:RunSummary.final_ready = $finalReady
  $script:RunSummary.CONTINUE_RUNNER_READY = $true

  $completedPayload = [ordered]@{
    task_id = $taskId
    page_key = $page
    completed_at = Now-Utc
    queue_seen = $true
    queue_started = $true
    single_runner_lock_acquired = $true
    task_runs_in_clean_worktree = $true
    allowed_paths_enforced = $true
    runner_output_uploaded = $true
    post_sync_ok = $true
    PUSH_SYNC_OK = $true
    CONTINUE_RUNNER_READY = $true
    browser_environment = $browserGate
    final_gate = $finalGate
    final_ready = $finalReady
    fake_data = $false
    blockers = @($script:RunSummary.blockers)
  }
  Write-TaskFile $worktree $completedRel (Json $completedPayload)
  $queueDone = [ordered]@{
    task_id = $taskId
    page_key = $page
    status = 'done'
    runner_completed_at = Now-Utc
    original_queue_file = $Task.queue_rel
    script_path = $Task.script_path
    target_branch = $Task.target_branch
    allowed_paths = $Task.allowed_paths
    no_fake_final_ready = $true
    no_db_write = $true
    no_migration = $true
    no_production_deploy = $true
    PUSH_SYNC_OK = $true
    CONTINUE_RUNNER_READY = $true
    final_ready = $finalReady
  }
  Write-TaskFile $worktree $Task.queue_rel (Json $queueDone)
  Write-TaskFile $worktree $heartbeatRel ("TASK_ID=$taskId`nPAGE_KEY=$page`nRUNNER_TOUCHED=true`nHEARTBEAT_AT=$(Now-Utc)`nSTATUS=completed`nPUSH_SYNC_OK=true`nCONTINUE_RUNNER_READY=true`n")

  $stage2 = Stage-AllowedChanges $worktree $allowed
  if (-not $stage2.ok) { throw 'BLOCKED_UNSCOPED_CHANGES: ' + ([string]::Join(',', $stage2.unscoped)) }
  Push-Location -LiteralPath $worktree
  try {
    $cached2Result = Invoke-AaysGit diff --cached --name-only
    Assert-GitOk $cached2Result 'BLOCKED_COMPLETION_GIT_DIFF_FAILED'
    $cached2 = ($cached2Result.output | Out-String).Trim()
    if ($cached2) {
      $commit2 = Invoke-AaysGit commit -m ("AAYS shared runner completion " + $page + " " + $taskId)
      Assert-GitOk $commit2 'BLOCKED_COMPLETION_COMMIT_FAILED'
      $fetch2 = Invoke-AaysGit fetch origin $Task.target_branch
      Assert-GitOk $fetch2 'BLOCKED_COMPLETION_FETCH_FAILED'
      $rebase2 = Invoke-AaysGit rebase ('origin/' + $Task.target_branch)
      if ($rebase2.code -ne 0) { throw 'BLOCKED_REBASE_CONFLICT: ' + $rebase2.output }
      $push2 = Invoke-AaysGit push origin ('HEAD:' + $Task.target_branch)
      Assert-GitOk $push2 'BLOCKED_COMPLETION_PUSH_FAILED'
    }
  } finally { Pop-Location }

  return $completedPayload
}

$RepoRoot = Full-Path $RepoRoot
if (-not (Test-Path -LiteralPath $RepoRoot)) { throw 'RepoRoot missing: ' + $RepoRoot }
if (-not (Test-Path -LiteralPath (Join-Path $RepoRoot '.git'))) { throw 'RepoRoot is not a git repo: ' + $RepoRoot }
Set-Location -LiteralPath $RepoRoot

$SharedRoot = Join-Path $RepoRoot 'docs\chatgpt_status\_shared'
$SharedStatusDir = Join-Path $SharedRoot 'status'
$SharedReportsDir = Join-Path $SharedRoot 'reports'
$SharedHeartbeatDir = Join-Path $SharedRoot 'heartbeat'
$SharedLockDir = Join-Path $SharedRoot 'runner_lock'
$SharedLogDir = Join-Path $SharedRoot 'logs'
foreach ($d in @($SharedStatusDir,$SharedReportsDir,$SharedHeartbeatDir,$SharedLockDir,$SharedLogDir)) { Ensure-Dir $d }
$script:GitLogPath = Join-Path $SharedLogDir ('git_invocations_' + (Get-Date -Format 'yyyyMMdd_HHmmss') + '.log')
$LockPath = Join-Path $SharedLockDir 'MULTI_PAGE.lock'
$RunnerHeartbeatPath = Join-Path $SharedHeartbeatDir 'MULTI_PAGE_heartbeat_latest.json'

if (Test-Path -LiteralPath $LockPath) {
  $stale = $true
  $lockRaw = Get-Content -LiteralPath $LockPath -Raw -ErrorAction SilentlyContinue
  try {
    $lock = $lockRaw | ConvertFrom-Json
    if ($lock.heartbeat_path -and (Test-Path -LiteralPath $lock.heartbeat_path)) {
      $age = (Get-Date) - (Get-Item -LiteralPath $lock.heartbeat_path).LastWriteTime
      $stale = ($age.TotalMinutes -gt $StaleMinutes)
    }
  } catch {}
  $payload = [ordered]@{ status = if($stale){'STALE_LOCK_DETECTED'}else{'RUNNER_LOCK_ACTIVE'}; lock_path=$LockPath; lock_raw=$lockRaw; stale=$stale; checked_at=Now-Utc; final_ready=$false; blocker=if($stale){'STALE_LOCK_REPORTED_NOT_DELETED'}else{'SINGLE_RUNNER_ALREADY_ACTIVE'} }
  Write-SharedReport ('MULTI_PAGE_lock_' + (Get-Date -Format 'yyyyMMdd_HHmmss') + '.json') $payload
  Write-SharedStatus 'MULTI_PAGE_latest_status.json' $payload
  Write-Output (Json $payload)
  exit 0
}

$lockPayload = [ordered]@{ pid=$PID; repo_root=$RepoRoot; started_at=Now-Utc; heartbeat_path=$RunnerHeartbeatPath; lock_path=$LockPath; runner='RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER' }
Write-Utf8 $LockPath (Json $lockPayload)
Write-Utf8 $RunnerHeartbeatPath (Json $lockPayload)
$script:RunSummary.single_runner_lock_acquired = $true

try {
  $fetchMain = Invoke-AaysGit fetch origin $MainBranch
  if ($fetchMain.code -ne 0) { Add-Blocker 'BLOCKED_MAIN_FETCH_FAILED' }

  $queueFiles = @(Get-ChildItem -Path (Join-Path $RepoRoot 'docs\chatgpt_status') -Recurse -File -ErrorAction SilentlyContinue | Where-Object { $_.FullName -match '[\\/]queue[\\/]' -and $_.Extension -in @('.json','.txt') })
  $script:RunSummary.queue_seen = ($queueFiles.Count -gt 0)
  if ($queueFiles.Count -eq 0) {
    Add-Blocker 'NO_QUEUE_ITEMS_FOUND'
    Write-SharedStatus 'MULTI_PAGE_latest_status.json' $script:RunSummary
    Write-Output (Json $script:RunSummary)
    exit 0
  }

  $validated = @()
  foreach ($qf in $queueFiles) {
    try {
      $parsed = Read-QueueFile $qf
      $v = Validate-Queue $qf $parsed.data
      $validated += $v
    } catch {
      Add-Blocker 'QUEUE_PARSE_FAILED'
    }
  }

  $readyStatuses = @('queued','pending','retry_pending','failed_transient')
  $ready = @($validated | Where-Object { $_.valid -and ($readyStatuses -contains ([string]$_.status).ToLowerInvariant()) } | Sort-Object queue_rel)
  if ($ready.Count -eq 0) {
    Add-Blocker 'NO_VALID_PENDING_QUEUE_ITEMS'
    $payload = [ordered]@{ summary=$script:RunSummary; invalid_count=@($validated | Where-Object { -not $_.valid }).Count; queue_seen=$true; final_ready=$false; checked_at=Now-Utc }
    Write-SharedStatus 'MULTI_PAGE_latest_status.json' $payload
    Write-SharedReport ('MULTI_PAGE_no_valid_queue_' + (Get-Date -Format 'yyyyMMdd_HHmmss') + '.json') $payload
    Write-Output (Json $payload)
    exit 0
  }

  $processed = @()
  foreach ($task in ($ready | Select-Object -First $MaxTasks)) {
    Write-Utf8 $RunnerHeartbeatPath (Json ([ordered]@{ pid=$PID; repo_root=$RepoRoot; updated_at=Now-Utc; current_task=$task.task_id; page_key=$task.page_key; heartbeat_path=$RunnerHeartbeatPath }))
    try {
      $processed += (Process-QueueTask $task)
    } catch {
      $err = $_.Exception.Message
      if ($err -match 'BLOCKED_REBASE_CONFLICT') { Add-Blocker 'BLOCKED_REBASE_CONFLICT' }
      elseif ($err -match 'BLOCKED_GITHUB_AUTH') { Add-Blocker 'BLOCKED_GITHUB_AUTH' }
      elseif ($err -match 'BLOCKED_UNSCOPED_CHANGES') { Add-Blocker 'BLOCKED_UNSCOPED_CHANGES' }
      elseif ($err -match 'BLOCKED_BROWSER_ENVIRONMENT') { Add-Blocker 'BLOCKED_BROWSER_ENVIRONMENT' }
      else { Add-Blocker 'RUNNER_TASK_FAILED' }
      $page = if($task.page_key){$task.page_key}else{'_shared'}
      $repDir = Join-Path $RepoRoot "docs/chatgpt_status/$page/reports"
      Ensure-Dir $repDir
      $failPayload = [ordered]@{ task_id=$task.task_id; page_key=$task.page_key; failed_at=Now-Utc; error=$err; final_ready=$false; fake_data=$false; blockers=$script:RunSummary.blockers }
      Write-Utf8 (Join-Path $repDir ($task.task_id + '_runner_failed.json')) (Json $failPayload)
    }
  }

  $final = [ordered]@{
    checked_at = Now-Utc
    queue_seen = $script:RunSummary.queue_seen
    queue_started = $script:RunSummary.queue_started
    single_runner_lock_acquired = $script:RunSummary.single_runner_lock_acquired
    task_runs_in_clean_worktree = $script:RunSummary.task_runs_in_clean_worktree
    allowed_paths_enforced = $script:RunSummary.allowed_paths_enforced
    runner_output_uploaded = $script:RunSummary.runner_output_uploaded
    post_sync_ok = $script:RunSummary.post_sync_ok
    PUSH_SYNC_OK = $script:RunSummary.PUSH_SYNC_OK
    CONTINUE_RUNNER_READY = $script:RunSummary.CONTINUE_RUNNER_READY
    final_ready = $script:RunSummary.final_ready
    blockers = @($script:RunSummary.blockers)
    processed = $processed
  }
  Write-SharedStatus 'MULTI_PAGE_latest_status.json' $final
  Write-SharedReport ('MULTI_PAGE_runner_output_' + (Get-Date -Format 'yyyyMMdd_HHmmss') + '.json') $final
  Write-Output (Json $final)
} finally {
  if (Test-Path -LiteralPath $LockPath) {
    try {
      $current = Get-Content -LiteralPath $LockPath -Raw | ConvertFrom-Json
      if ([int]$current.pid -eq [int]$PID) { Remove-Item -LiteralPath $LockPath -Force -ErrorAction SilentlyContinue }
    } catch {}
  }
}
