[CmdletBinding()]
param(
  [string]$RepoRoot,
  [switch]$EnsurePageDirs
)

$ErrorActionPreference = "Stop"

function Get-DefaultRepoRoot {
  $candidate = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..\..\..")
  return $candidate.Path
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
    if (-not (Test-Path -LiteralPath $Path)) { return $null }
    $text = Get-Content -Raw -LiteralPath $Path
    if ([string]::IsNullOrWhiteSpace($text)) { return $null }
    return $text | ConvertFrom-Json -ErrorAction Stop
  } catch {
    return $null
  }
}

function Get-JsonValue {
  param(
    [object]$Object,
    [string[]]$Names,
    [object]$Default = $null
  )
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

function Get-LatestFile {
  param(
    [string[]]$Directories,
    [string[]]$Patterns = @("*")
  )
  $files = @()
  foreach ($dir in $Directories) {
    if (-not (Test-Path -LiteralPath $dir)) { continue }
    foreach ($pattern in $Patterns) {
      $files += Get-ChildItem -LiteralPath $dir -File -Filter $pattern -ErrorAction SilentlyContinue
    }
  }
  return $files | Sort-Object LastWriteTime -Descending | Select-Object -First 1
}

function Get-QueueFiles {
  param([string]$QueueDir)
  if (-not (Test-Path -LiteralPath $QueueDir)) { return @() }
  return @(Get-ChildItem -LiteralPath $QueueDir -File -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -notlike ".*" } |
    Sort-Object @{ Expression = { if ($_.Name -eq "current.task.json") { 0 } else { 1 } } }, LastWriteTime -Descending)
}

function Get-PercentFromText {
  param([string]$Text, [string[]]$Names)
  if ([string]::IsNullOrWhiteSpace($Text)) { return $null }
  foreach ($name in $Names) {
    $pattern = "(?im)\b$([regex]::Escape($name))\b\s*[:=]\s*(\d{1,3})"
    $m = [regex]::Match($Text, $pattern)
    if ($m.Success) {
      $value = [int]$m.Groups[1].Value
      if ($value -lt 0) { $value = 0 }
      if ($value -gt 100) { $value = 100 }
      return $value
    }
  }
  return $null
}

function Get-PercentFromEvidence {
  param([System.IO.FileInfo[]]$Files)
  foreach ($file in $Files) {
    if ($null -eq $file -or -not (Test-Path -LiteralPath $file.FullName)) { continue }
    $json = Read-JsonFile -Path $file.FullName
    if ($null -ne $json) {
      $value = Get-JsonValue -Object $json -Names @("completion_percent", "COMPLETION_PERCENT", "product_completion_percent")
      if ($null -ne $value) {
        $int = [int]$value
        if ($int -lt 0) { $int = 0 }
        if ($int -gt 100) { $int = 100 }
        return $int
      }
    }
    try {
      $text = Get-Content -Raw -LiteralPath $file.FullName -ErrorAction Stop
      $parsed = Get-PercentFromText -Text $text -Names @("completion_percent", "COMPLETION_PERCENT", "product_completion_percent")
      if ($null -ne $parsed) { return $parsed }
    } catch {
      continue
    }
  }
  return 0
}

function Get-BlockersFromEvidence {
  param([System.IO.FileInfo[]]$Files)
  $blockers = New-Object System.Collections.Generic.List[string]
  foreach ($file in $Files) {
    if ($null -eq $file -or -not (Test-Path -LiteralPath $file.FullName)) { continue }
    $json = Read-JsonFile -Path $file.FullName
    if ($null -ne $json) {
      $jsonBlockers = Get-JsonValue -Object $json -Names @("blockers", "BLOCKERS")
      if ($null -ne $jsonBlockers) {
        foreach ($b in @($jsonBlockers)) {
          if (-not [string]::IsNullOrWhiteSpace([string]$b)) { $blockers.Add([string]$b) }
        }
      }
      $blocker = Get-JsonValue -Object $json -Names @("blocker", "BLOCKER", "latest_blocker")
      if (-not [string]::IsNullOrWhiteSpace([string]$blocker) -and [string]$blocker -ne "none") {
        $blockers.Add([string]$blocker)
      }
    }
    try {
      $text = Get-Content -Raw -LiteralPath $file.FullName -ErrorAction Stop
      foreach ($m in [regex]::Matches($text, "(?im)^\s*BLOCKER\s*[:=]\s*(.+)$")) {
        $value = $m.Groups[1].Value.Trim()
        if ($value -and $value -ne "none") { $blockers.Add($value) }
      }
    } catch {
      continue
    }
  }
  return @($blockers | Select-Object -Unique)
}

function Get-HeartbeatTime {
  param([System.IO.FileInfo]$File)
  if ($null -eq $File) { return $null }
  $json = Read-JsonFile -Path $File.FullName
  if ($null -ne $json) {
    $value = Get-JsonValue -Object $json -Names @("heartbeat_at", "HEARTBEAT_AT", "checked_at", "updated_at")
    if ($null -ne $value) { return [string]$value }
  }
  try {
    $text = Get-Content -Raw -LiteralPath $File.FullName -ErrorAction Stop
    $m = [regex]::Match($text, "(?im)^\s*(HEARTBEAT_AT|checked_at|updated_at)\s*[:=]\s*(.+)$")
    if ($m.Success) { return $m.Groups[2].Value.Trim() }
  } catch {
  }
  return $File.LastWriteTimeUtc.ToString("o")
}

function Get-DisplayName {
  param([string]$PageKey)
  if ($script:DisplayNames.ContainsKey($PageKey)) { return $script:DisplayNames[$PageKey] }
  return $PageKey
}

if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
  $RepoRoot = Get-DefaultRepoRoot
}
$script:RepoRoot = [System.IO.Path]::GetFullPath($RepoRoot)
$chatRoot = Join-RepoPath "docs/chatgpt_status"
$sharedRoot = Join-Path $chatRoot "_shared"

$requiredSharedDirs = @("contracts", "templates", "panel", "status", "reports", "state", "heartbeat", "page_registry", "lock", "runner_lock", "queue", "completed", "blocked")
foreach ($dir in $requiredSharedDirs) {
  New-Item -ItemType Directory -Force -Path (Join-Path $sharedRoot $dir) | Out-Null
}
New-Item -ItemType Directory -Force -Path (Join-RepoPath "england_map_web/data/runner_panel") | Out-Null

$script:DisplayNames = @{}
$menuRegistryPath = Join-Path $sharedRoot "automation/aays_runner_pages.json"
$menuRegistry = Read-JsonFile -Path $menuRegistryPath
$seedPages = New-Object System.Collections.Generic.List[string]
foreach ($seed in @(
  "aays1",
  "topography",
  "distance_property_types",
  "gas_emissions",
  "internet_access_parcel_layer_low_credit_20260612",
  "security_public_safety",
  "security_public_safety_low_credit_20260612",
  "AAYS_REAL_TOPOGRAPHY_PRODUCT"
)) {
  $seedPages.Add($seed)
}
if ($null -ne $menuRegistry) {
  foreach ($menuPage in @($menuRegistry.pages)) {
    $key = [string]$menuPage.page_key
    if ($key) {
      $seedPages.Add($key)
      $script:DisplayNames[$key] = [string]$menuPage.display_name
    }
  }
}

$pageSet = [ordered]@{}
foreach ($page in $seedPages) {
  if (-not [string]::IsNullOrWhiteSpace($page)) { $pageSet[$page] = $true }
}
if (Test-Path -LiteralPath $chatRoot) {
  foreach ($dir in Get-ChildItem -LiteralPath $chatRoot -Directory -ErrorAction SilentlyContinue) {
    if ($dir.Name -eq "_shared") { continue }
    $pageSet[$dir.Name] = $true
  }
}

$pageDirNames = @("queue", "status", "reports", "heartbeat", "completed", "blocked", "runner_outputs", "automation", "fixtures", "runner_tasks")
$pages = New-Object System.Collections.Generic.List[object]
$registryPages = New-Object System.Collections.Generic.List[object]

foreach ($pageKey in $pageSet.Keys) {
  $pageRoot = Join-Path $chatRoot $pageKey
  if ($EnsurePageDirs) {
    New-Item -ItemType Directory -Force -Path $pageRoot | Out-Null
    foreach ($dirName in $pageDirNames) {
      New-Item -ItemType Directory -Force -Path (Join-Path $pageRoot $dirName) | Out-Null
    }
  }

  $queueDir = Join-Path $pageRoot "queue"
  $statusDir = Join-Path $pageRoot "status"
  $reportsDir = Join-Path $pageRoot "reports"
  $heartbeatDir = Join-Path $pageRoot "heartbeat"
  $completedDir = Join-Path $pageRoot "completed"
  $blockedDir = Join-Path $pageRoot "blocked"
  $runnerOutputsDir = Join-Path $pageRoot "runner_outputs"
  $automationDir = Join-Path $pageRoot "automation"
  $fixturesDir = Join-Path $pageRoot "fixtures"
  $runnerTasksDir = Join-Path $pageRoot "runner_tasks"

  $queueFiles = Get-QueueFiles -QueueDir $queueDir
  $latestQueue = $queueFiles | Select-Object -First 1
  $queue = $null
  $queueErrors = New-Object System.Collections.Generic.List[string]
  $latestTaskId = ""
  $latestQueueStatus = "unknown"
  $scriptPath = ""
  $automationScript = ""
  $allowedPaths = @()

  if ($null -ne $latestQueue) {
    $queue = Read-JsonFile -Path $latestQueue.FullName
    if ($null -eq $queue) {
      $queueErrors.Add("queue_not_json_or_unreadable")
      $latestTaskId = [System.IO.Path]::GetFileNameWithoutExtension($latestQueue.Name)
    } else {
      $latestTaskId = [string](Get-JsonValue -Object $queue -Names @("task_id", "taskId") -Default ([System.IO.Path]::GetFileNameWithoutExtension($latestQueue.Name)))
      $latestQueueStatus = [string](Get-JsonValue -Object $queue -Names @("status") -Default "unknown")
      $payloadPageKey = [string](Get-JsonValue -Object $queue -Names @("page_key", "pageKey") -Default "")
      if ([string]::IsNullOrWhiteSpace($payloadPageKey)) {
        $queueErrors.Add("missing_page_key")
      } elseif ($payloadPageKey -ne $pageKey) {
        $queueErrors.Add("PAGE_KEY_PATH_MISMATCH")
      }

      $scriptPath = [string](Get-JsonValue -Object $queue -Names @("script_path", "scriptPath") -Default "")
      $automationScript = [string](Get-JsonValue -Object $queue -Names @("automation_script", "script") -Default "")
      if ([string]::IsNullOrWhiteSpace($scriptPath)) { $queueErrors.Add("missing_script_path") }
      if ([string]::IsNullOrWhiteSpace($automationScript)) { $queueErrors.Add("missing_automation_script") }
      if ($scriptPath -and $automationScript -and $scriptPath -ne $automationScript) { $queueErrors.Add("script_path_automation_script_mismatch") }

      $allowedPathsValue = Get-JsonValue -Object $queue -Names @("allowed_paths", "allowedPaths")
      if ($null -eq $allowedPathsValue -or @($allowedPathsValue).Count -eq 0) {
        $queueErrors.Add("missing_allowed_paths")
      } else {
        $allowedPaths = @($allowedPathsValue | ForEach-Object { [string]$_ })
      }

      foreach ($flag in @("no_fake_final_ready", "no_db_write", "no_migration", "no_production_deploy")) {
        if (-not (ConvertTo-SafeBool -Value (Get-JsonValue -Object $queue -Names @($flag)) -Default $false)) {
          $queueErrors.Add("missing_or_false_$flag")
        }
      }
      if ((ConvertTo-SafeBool -Value (Get-JsonValue -Object $queue -Names @("final_ready", "finalReady")) -Default $false)) {
        $queueErrors.Add("final_ready_true_requires_gate_evidence")
      }
    }
  }

  $latestHeartbeat = Get-LatestFile -Directories @($heartbeatDir, $statusDir) -Patterns @("*heartbeat*", "heartbeat_latest.txt")
  $latestCompleted = Get-LatestFile -Directories @($completedDir) -Patterns @("*completed*", "*.completed.json")
  $latestBlocked = Get-LatestFile -Directories @($blockedDir, $statusDir) -Patterns @("*blocked*")
  $latestReport = Get-LatestFile -Directories @($reportsDir, $runnerOutputsDir) -Patterns @("*report*", "*runner_output*", "*.md", "*.txt", "*.json")
  $latestStatus = Get-LatestFile -Directories @($statusDir) -Patterns @("*.json", "*.txt")

  $evidenceFiles = @($latestQueue, $latestHeartbeat, $latestCompleted, $latestBlocked, $latestReport, $latestStatus) |
    Where-Object { $null -ne $_ }
  $completionPercent = Get-PercentFromEvidence -Files $evidenceFiles
  $remainingPercent = 100 - $completionPercent
  if ($remainingPercent -lt 0) { $remainingPercent = 0 }

  $blockers = New-Object System.Collections.Generic.List[string]
  foreach ($err in $queueErrors) { $blockers.Add($err) }
  foreach ($b in (Get-BlockersFromEvidence -Files $evidenceFiles)) { $blockers.Add($b) }
  if ($null -ne $latestQueue -and $null -eq $latestHeartbeat) {
    $blockers.Add("missing_github_visible_runner_lifecycle_output")
  }
  $blockerList = @($blockers | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Select-Object -Unique)

  $finalReady = $false
  $completedJson = if ($null -ne $latestCompleted) { Read-JsonFile -Path $latestCompleted.FullName } else { $null }
  if ($null -ne $completedJson) {
    $completedFinalReady = ConvertTo-SafeBool -Value (Get-JsonValue -Object $completedJson -Names @("final_ready", "finalReady")) -Default $false
    $runnerOutputUploaded = ConvertTo-SafeBool -Value (Get-JsonValue -Object $completedJson -Names @("runner_output_uploaded")) -Default $false
    $pushOk = ConvertTo-SafeBool -Value (Get-JsonValue -Object $completedJson -Names @("PUSH_SYNC_OK", "push_sync_ok")) -Default $false
    $finalReady = ($completedFinalReady -and $runnerOutputUploaded -and $pushOk)
  }

  $runnerStatus = "Bekliyor"
  if ($blockerList.Count -gt 0) {
    $runnerStatus = "Problem"
  } elseif ($latestQueueStatus -match '^(queued|ready|pending|pending_repo_queue|pickup_requested|queued_for_single_shared_runner|retry_pending)$') {
    $runnerStatus = "Bekliyor"
  } elseif ($latestQueueStatus -match '^(running)$') {
    $runnerStatus = "Calisiyor"
  } elseif ($latestHeartbeat) {
    $runnerStatus = "Runner Aktif"
  }

  $evidencePaths = @($evidenceFiles | ForEach-Object { ConvertTo-RepoRelative -Path $_.FullName } | Select-Object -Unique)
  $entry = [ordered]@{
    page_key = $pageKey
    display_name = Get-DisplayName -PageKey $pageKey
    runner_status = $runnerStatus
    latest_queue_status = $latestQueueStatus
    latest_task_id = $latestTaskId
    latest_queue_task = if ($latestQueue) { ConvertTo-RepoRelative -Path $latestQueue.FullName } else { "" }
    completion_percent = [int]$completionPercent
    remaining_percent = [int]$remainingPercent
    final_ready = [bool]$finalReady
    last_heartbeat_at = Get-HeartbeatTime -File $latestHeartbeat
    heartbeat_at = Get-HeartbeatTime -File $latestHeartbeat
    last_completed_at = if ($latestCompleted) { $latestCompleted.LastWriteTimeUtc.ToString("o") } else { $null }
    latest_report = if ($latestReport) { ConvertTo-RepoRelative -Path $latestReport.FullName } else { "" }
    latest_blocker = if ($blockerList.Count -gt 0) { [string]$blockerList[0] } else { "" }
    blockers = @($blockerList)
    evidence_paths = @($evidencePaths)
    runner_contract_valid = ($queueErrors.Count -eq 0)
    queue_contract_errors = @($queueErrors)
    queue_file_count = @($queueFiles).Count
    menu_name = Get-DisplayName -PageKey $pageKey
    single_runner_status = $runnerStatus
    runner_mode = "single_shared_runner"
    directories = [ordered]@{
      root = ConvertTo-RepoRelative -Path $pageRoot
      queue = ConvertTo-RepoRelative -Path $queueDir
      status = ConvertTo-RepoRelative -Path $statusDir
      reports = ConvertTo-RepoRelative -Path $reportsDir
      heartbeat = ConvertTo-RepoRelative -Path $heartbeatDir
      completed = ConvertTo-RepoRelative -Path $completedDir
      blocked = ConvertTo-RepoRelative -Path $blockedDir
      runner_outputs = ConvertTo-RepoRelative -Path $runnerOutputsDir
      automation = ConvertTo-RepoRelative -Path $automationDir
      fixtures = ConvertTo-RepoRelative -Path $fixturesDir
      runner_tasks = ConvertTo-RepoRelative -Path $runnerTasksDir
    }
  }
  $pages.Add([pscustomobject]$entry)

  $registryPages.Add([pscustomobject]([ordered]@{
    page_key = $pageKey
    display_name = Get-DisplayName -PageKey $pageKey
    root = "docs/chatgpt_status/$pageKey"
    queue_dir = "docs/chatgpt_status/$pageKey/queue"
    status_dir = "docs/chatgpt_status/$pageKey/status"
    report_dir = "docs/chatgpt_status/$pageKey/reports"
    reports_dir = "docs/chatgpt_status/$pageKey/reports"
    heartbeat_dir = "docs/chatgpt_status/$pageKey/heartbeat"
    completed_dir = "docs/chatgpt_status/$pageKey/completed"
    blocked_dir = "docs/chatgpt_status/$pageKey/blocked"
    runner_outputs_dir = "docs/chatgpt_status/$pageKey/runner_outputs"
    automation_dir = "docs/chatgpt_status/$pageKey/automation"
    fixtures_dir = "docs/chatgpt_status/$pageKey/fixtures"
    runner_tasks_dir = "docs/chatgpt_status/$pageKey/runner_tasks"
    canonical_queue = "docs/chatgpt_status/$pageKey/queue/current.task.json"
    heartbeat_file = "docs/chatgpt_status/$pageKey/status/heartbeat_latest.txt"
    allowed_paths = @("docs/chatgpt_status/$pageKey/")
    final_ready_policy = "real_evidence_only"
  }))
}

$lockPath = Join-Path $sharedRoot "state/single_runner.lock.json"
$runnerPid = $null
$runnerActive = $false
if (Test-Path -LiteralPath $lockPath) {
  $lock = Read-JsonFile -Path $lockPath
  if ($null -ne $lock) {
    $pidValue = Get-JsonValue -Object $lock -Names @("pid", "runner_pid")
    if ($pidValue) {
      $runnerPid = [int]$pidValue
      $runnerActive = $null -ne (Get-Process -Id $runnerPid -ErrorAction SilentlyContinue)
    }
  }
}

$generatedAt = (Get-Date).ToUniversalTime().ToString("o")
$branchName = "unknown"
try {
  $branchOutput = & git -C $script:RepoRoot rev-parse --abbrev-ref HEAD 2>$null
  if (-not [string]::IsNullOrWhiteSpace([string]$branchOutput)) { $branchName = [string]$branchOutput }
} catch {
  $branchName = "unknown"
}
$pageArray = @($pages.ToArray())
$registryPageArray = @($registryPages.ToArray())
$singleRunnerStatus = if ($runnerActive) { "active" } else { "idle_or_not_running" }
$menuMappings = @()
if ($null -ne $menuRegistry) {
  $menuMappings = @($menuRegistry.pages | ForEach-Object {
    [pscustomobject]([ordered]@{
      display_name = [string]$_.display_name
      menu_name = [string]$_.display_name
      page_key = [string]$_.page_key
      aliases = @($_.aliases)
    })
  })
}
$index = [ordered]@{
  generated_at = $generatedAt
  updated_at = $generatedAt
  last_checked_at = $generatedAt
  runner_contract_version = "single_shared_runner_v1"
  runner_mode = "single_shared_runner"
  repo_root = $script:RepoRoot
  repo_full_name = "cagdascagdas100/chat_gpt_clone_1"
  branch = $branchName
  main_branch = "main"
  single_runner_active = [bool]$runnerActive
  single_runner_status = $singleRunnerStatus
  runner_pid = $runnerPid
  github_push_status = "not_attempted_by_panel_builder"
  repo_root_compatibility = [ordered]@{
    active_repo_root = $script:RepoRoot
    c_drive_checkout_supported = (Test-Path -LiteralPath "C:\Users\cagda\Documents\GitHub\AAYS")
    f_drive_main_supported = (Test-Path -LiteralPath "F:\chatgpt\chat_gpt_clone_1_main")
    f_drive_fresh_supported = (Test-Path -LiteralPath "F:\chatgpt\chat_gpt_clone_1_main_fresh")
  }
  menu_mappings = @($menuMappings)
  pages = $pageArray
}

$registry = [ordered]@{
  project_family = "AAYS"
  default_branch = "main"
  repo_full_name = "cagdascagdas100/chat_gpt_clone_1"
  runner_mode = "single_shared_runner"
  generated_at = $generatedAt
  repo_root = $script:RepoRoot
  branch = $branchName
  pages = $registryPageArray
  menu_mappings = @($menuMappings)
}

$jsonDepth = 12
$panelIndexPath = Join-Path $sharedRoot "panel/page_status_index_latest.json"
$statusIndexPath = Join-Path $sharedRoot "status/page_panel_index.json"
$dashboardPath = Join-Path $sharedRoot "status/pages_status_dashboard.json"
$webPanelPath = Join-RepoPath "england_map_web/data/runner_panel/page_status_index.json"
$registryPath = Join-Path $sharedRoot "contracts/PAGE_KEY_REGISTRY.json"
$registryAliasPath = Join-Path $sharedRoot "page_registry.json"
$manifestPath = Join-Path $sharedRoot "page_registry/pages_manifest.json"
$inventoryJsonPath = Join-Path $sharedRoot "status/page_contract_inventory_20260706.json"
$inventoryMdPath = Join-Path $sharedRoot "reports/page_contract_inventory_20260706.md"

$index | ConvertTo-Json -Depth $jsonDepth | Set-Content -LiteralPath $panelIndexPath -Encoding UTF8
$index | ConvertTo-Json -Depth $jsonDepth | Set-Content -LiteralPath $statusIndexPath -Encoding UTF8
$index | ConvertTo-Json -Depth $jsonDepth | Set-Content -LiteralPath $dashboardPath -Encoding UTF8
$index | ConvertTo-Json -Depth $jsonDepth | Set-Content -LiteralPath $webPanelPath -Encoding UTF8
$registry | ConvertTo-Json -Depth $jsonDepth | Set-Content -LiteralPath $registryPath -Encoding UTF8
$registry | ConvertTo-Json -Depth $jsonDepth | Set-Content -LiteralPath $registryAliasPath -Encoding UTF8
$registry | ConvertTo-Json -Depth $jsonDepth | Set-Content -LiteralPath $manifestPath -Encoding UTF8
$index | ConvertTo-Json -Depth $jsonDepth | Set-Content -LiteralPath $inventoryJsonPath -Encoding UTF8

$invalidPages = @($pageArray | Where-Object { -not $_.runner_contract_valid }).Count
$md = New-Object System.Collections.Generic.List[string]
$md.Add("# AAYS Page Contract Inventory 20260706")
$md.Add("")
$md.Add("Generated: $generatedAt")
$md.Add("Repo: cagdascagdas100/chat_gpt_clone_1")
$md.Add("Branch: main")
$md.Add("Runner contract: single_shared_runner_v1")
$md.Add("")
$md.Add("- pages_detected: $($pageArray.Count)")
$md.Add("- pages_with_queue_contract_errors: $invalidPages")
$md.Add("- fake_data: false")
$md.Add("- db_write: false")
$md.Add("- migration: false")
$md.Add("- production_deploy: false")
$md.Add("")
$md.Add("| page_key | display_name | queue_status | percent | final_ready | blocker |")
$md.Add("| --- | --- | --- | ---: | --- | --- |")
foreach ($page in ($pageArray | Sort-Object page_key)) {
  $blocker = if ($page.blockers.Count -gt 0) { ($page.blockers -join "; ") } else { "" }
  $md.Add("| $($page.page_key) | $($page.display_name) | $($page.latest_queue_status) | $($page.completion_percent) | $($page.final_ready) | $blocker |")
}
$md | Set-Content -LiteralPath $inventoryMdPath -Encoding UTF8

[pscustomobject]@{
  generated_at = $generatedAt
  page_count = $pageArray.Count
  invalid_page_count = $invalidPages
  panel_index = ConvertTo-RepoRelative -Path $panelIndexPath
  registry = ConvertTo-RepoRelative -Path $registryPath
  web_panel_data = ConvertTo-RepoRelative -Path $webPanelPath
} | ConvertTo-Json -Depth 6
