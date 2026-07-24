[CmdletBinding()]
param(
  [string]$RepoRoot,
  [switch]$WriteAliases
)

$ErrorActionPreference = "Stop"

function Get-DefaultRepoRoot {
  return (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..\..\..")).Path
}

function ConvertTo-RepoRelative {
  param([string]$Path)
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

function Convert-Status {
  param([string]$Status)
  if ([string]::IsNullOrWhiteSpace($Status)) { return "queued" }
  switch -Regex ($Status.ToLowerInvariant()) {
    '^(done|finish|finished|completed|done_on_target_branch)$' { return "completed" }
    '^(blocked|blocked_manual)$' { return "blocked" }
    '^(failed|failed_final)$' { return "failed" }
    default { return $Status }
  }
}

function Convert-Priority {
  param([object]$Value)
  $parsed = 100
  if ($null -eq $Value) { return $parsed }
  if ([int]::TryParse([string]$Value, [ref]$parsed)) { return $parsed }
  return 100
}

function New-NormalizedQueue {
  param(
    [System.IO.FileInfo]$QueueFile,
    [object]$Queue,
    [string]$PageKey
  )

  $taskId = [string](Get-JsonValue -Object $Queue -Names @("task_id", "taskId") -Default ([System.IO.Path]::GetFileNameWithoutExtension($QueueFile.Name)))
  $taskId = ($taskId -replace '[^A-Za-z0-9_.-]', '_')
  if ([string]::IsNullOrWhiteSpace($taskId)) { $taskId = "normalized_task" }

  $scriptPath = [string](Get-JsonValue -Object $Queue -Names @("script_path", "scriptPath"))
  $automationScript = [string](Get-JsonValue -Object $Queue -Names @("automation_script", "script"))
  if ([string]::IsNullOrWhiteSpace($scriptPath) -and -not [string]::IsNullOrWhiteSpace($automationScript)) {
    $scriptPath = $automationScript
  }
  if ([string]::IsNullOrWhiteSpace($automationScript) -and -not [string]::IsNullOrWhiteSpace($scriptPath)) {
    $automationScript = $scriptPath
  }
  $blockers = New-Object System.Collections.Generic.List[string]
  if ([string]::IsNullOrWhiteSpace($scriptPath) -and [string]::IsNullOrWhiteSpace($automationScript)) {
    $scriptPath = "docs/chatgpt_status/_shared/automation/SAFE_STATUS_ONLY_PAGE_TASK_20260706.ps1"
    $automationScript = $scriptPath
    $blockers.Add("MISSING_script_path_OR_automation_script")
  }

  $allowedPaths = Get-JsonValue -Object $Queue -Names @("allowed_paths", "allowedPaths")
  if ($null -eq $allowedPaths -or @($allowedPaths).Count -eq 0) {
    $allowedPaths = @("docs/chatgpt_status/$PageKey/")
    $blockers.Add("missing_allowed_paths_defaulted")
  }

  $payloadPageKey = [string](Get-JsonValue -Object $Queue -Names @("page_key", "pageKey") -Default $PageKey)
  if ($payloadPageKey -ne $PageKey) {
    $blockers.Add("PAGE_KEY_PATH_MISMATCH")
  }

  $status = Convert-Status -Status ([string](Get-JsonValue -Object $Queue -Names @("status") -Default "queued"))

  return [ordered]@{
    task_id = $taskId
    page_key = $PageKey
    status = $status
    priority = Convert-Priority -Value (Get-JsonValue -Object $Queue -Names @("priority") -Default 100)
    target_branch = [string](Get-JsonValue -Object $Queue -Names @("target_branch", "branch") -Default "main")
    script_path = $scriptPath
    automation_script = $automationScript
    allowed_paths = @($allowedPaths | ForEach-Object { [string]$_ })
    new_runner_allowed = $false
    single_shared_runner_required = $true
    no_fake_final_ready = $true
    no_db_write = $true
    no_migration = $true
    no_production_deploy = $true
    final_ready = $false
    legacy_source_path = ConvertTo-RepoRelative -Path $QueueFile.FullName
    normalized_from_invalid_contract = ($blockers.Count -gt 0)
    normalization_blockers = @($blockers)
    updated_at = (Get-Date).ToUniversalTime().ToString("o")
  }
}

if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
  $RepoRoot = Get-DefaultRepoRoot
}
$script:RepoRoot = [System.IO.Path]::GetFullPath($RepoRoot)
$chatRoot = Join-Path $script:RepoRoot "docs/chatgpt_status"
$sharedRoot = Join-Path $chatRoot "_shared"
New-Item -ItemType Directory -Force -Path (Join-Path $sharedRoot "reports") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $sharedRoot "status") | Out-Null

$results = New-Object System.Collections.Generic.List[object]
$queueFiles = @()
if (Test-Path -LiteralPath $chatRoot) {
  foreach ($pageDir in Get-ChildItem -LiteralPath $chatRoot -Directory -ErrorAction SilentlyContinue) {
    if ($pageDir.Name -eq "_shared") { continue }
    $queueDir = Join-Path $pageDir.FullName "queue"
    if (Test-Path -LiteralPath $queueDir) {
      $queueFiles += Get-ChildItem -LiteralPath $queueDir -File -ErrorAction SilentlyContinue
    }
  }
}

foreach ($file in $queueFiles) {
  $pageKey = $file.Directory.Parent.Name
  $queue = Read-JsonFile -Path $file.FullName
  $errors = New-Object System.Collections.Generic.List[string]
  if ($null -eq $queue) {
    $errors.Add("not_json_or_unreadable")
    $results.Add([pscustomobject]([ordered]@{
      source = ConvertTo-RepoRelative -Path $file.FullName
      page_key = $pageKey
      normalized_alias = ""
      normalized = $false
      errors = @($errors)
    }))
    continue
  }

  $normalized = New-NormalizedQueue -QueueFile $file -Queue $queue -PageKey $pageKey
  $needsAlias = [bool]$normalized.normalized_from_invalid_contract
  $sourcePageKey = [string](Get-JsonValue -Object $queue -Names @("page_key", "pageKey"))
  if ([string]::IsNullOrWhiteSpace($sourcePageKey)) { $needsAlias = $true; $errors.Add("missing_page_key") }
  if ([string]::IsNullOrWhiteSpace([string](Get-JsonValue -Object $queue -Names @("script_path", "scriptPath"))) -or
      [string]::IsNullOrWhiteSpace([string](Get-JsonValue -Object $queue -Names @("automation_script", "script")))) {
    $needsAlias = $true
    $errors.Add("missing_script_path_or_automation_script_alias")
  }
  if ($null -eq (Get-JsonValue -Object $queue -Names @("allowed_paths", "allowedPaths"))) {
    $needsAlias = $true
    $errors.Add("missing_allowed_paths")
  }
  foreach ($flag in @("no_fake_final_ready", "no_db_write", "no_migration", "no_production_deploy")) {
    $flagValue = Get-JsonValue -Object $queue -Names @($flag)
    if ($flagValue -ne $true) {
      $needsAlias = $true
      $errors.Add("missing_or_false_$flag")
    }
  }

  $aliasPath = ""
  if ($needsAlias) {
    $aliasName = "normalized_$($normalized.task_id)_20260706.json"
    $aliasPathFull = Join-Path $file.Directory.FullName $aliasName
    $aliasPath = ConvertTo-RepoRelative -Path $aliasPathFull
    if ($WriteAliases) {
      $normalized | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $aliasPathFull -Encoding UTF8
    }
  }

  $results.Add([pscustomobject]([ordered]@{
    source = ConvertTo-RepoRelative -Path $file.FullName
    page_key = $pageKey
    normalized_alias = $aliasPath
    normalized = [bool]($needsAlias -and $WriteAliases)
    would_normalize = [bool]$needsAlias
    errors = @($errors | Select-Object -Unique)
    normalized_status = $normalized.status
    final_ready = $false
  }))
}

$generatedAt = (Get-Date).ToUniversalTime().ToString("o")
$resultArray = @($results.ToArray())
$wouldNormalizeCount = @($resultArray | Where-Object { $_.would_normalize }).Count
$normalizedCount = @($resultArray | Where-Object { $_.normalized }).Count
$report = [ordered]@{
  generated_at = $generatedAt
  write_aliases = [bool]$WriteAliases
  scanned_queue_files = $queueFiles.Count
  would_normalize_count = $wouldNormalizeCount
  normalized_count = $normalizedCount
  fake_data = $false
  db_write = $false
  migration = $false
  production_deploy = $false
  results = $resultArray
}

$statusPath = Join-Path $sharedRoot "status/legacy_queue_normalization_result_20260706.json"
$latestPath = Join-Path $sharedRoot "status/queue_normalizer_latest.json"
$planMdPath = Join-Path $sharedRoot "reports/legacy_queue_normalization_plan_20260706.md"
$report | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $statusPath -Encoding UTF8
$report | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $latestPath -Encoding UTF8

$md = New-Object System.Collections.Generic.List[string]
$md.Add("# Legacy Queue Normalization Plan 20260706")
$md.Add("")
$md.Add("Generated: $generatedAt")
$md.Add("Write aliases: $([bool]$WriteAliases)")
$md.Add("")
$md.Add("- scanned_queue_files: $($queueFiles.Count)")
$md.Add("- would_normalize_count: $wouldNormalizeCount")
$md.Add("- normalized_count: $normalizedCount")
$md.Add("- fake_data: false")
$md.Add("- db_write: false")
$md.Add("- migration: false")
$md.Add("- production_deploy: false")
$md.Add("")
$md.Add("| source | page_key | alias | errors |")
$md.Add("| --- | --- | --- | --- |")
foreach ($row in $resultArray) {
  if (-not $row.would_normalize) { continue }
  $md.Add("| $($row.source) | $($row.page_key) | $($row.normalized_alias) | $($row.errors -join '; ') |")
}
$md | Set-Content -LiteralPath $planMdPath -Encoding UTF8

[pscustomobject]@{
  generated_at = $generatedAt
  scanned_queue_files = $queueFiles.Count
  would_normalize_count = $wouldNormalizeCount
  normalized_count = $normalizedCount
  result = ConvertTo-RepoRelative -Path $statusPath
} | ConvertTo-Json -Depth 6
