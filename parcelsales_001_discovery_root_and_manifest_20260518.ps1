$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$RunId = Get-Date -Format "yyyyMMdd_HHmmss"
$BridgeRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $BridgeRoot) { $BridgeRoot = (Get-Location).Path }
$OutRoot = Join-Path $BridgeRoot "ai-runner-outputs"
$OutDir = Join-Path $OutRoot "parcelsales_001_discovery_root_and_manifest_$RunId"
New-Item -ItemType Directory -Force $OutDir | Out-Null

function Test-PathSafe {
  param([string]$Path)
  try { return (Test-Path -LiteralPath $Path) } catch { return $false }
}

function Get-ItemInfoSafe {
  param([string]$Path)
  $exists = Test-PathSafe $Path
  $info = [ordered]@{ path = $Path; exists = $exists }
  if ($exists) {
    try {
      $item = Get-Item -LiteralPath $Path -Force
      $info["type"] = if ($item.PSIsContainer) { "directory" } else { "file" }
      $info["last_write_time"] = $item.LastWriteTime.ToString("s")
      if (-not $item.PSIsContainer) { $info["length_bytes"] = $item.Length }
    } catch {
      $info["error"] = $_.Exception.Message
    }
  }
  return $info
}

function Get-ChildNamesSafe {
  param([string]$Path, [int]$Limit = 80)
  if (-not (Test-PathSafe $Path)) { return @() }
  try {
    return @(Get-ChildItem -LiteralPath $Path -Force -ErrorAction Stop | Select-Object -First $Limit | ForEach-Object { $_.Name })
  } catch {
    return @("ERROR: $($_.Exception.Message)")
  }
}

$CandidateRoots = @(
  "C:\Users\cagda\Documents\GitHub\AAYS",
  "C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence",
  "C:\Users\cagda\Documents\chat_gpt_clone_1",
  "C:\AAYS_GITHUB_BRIDGE_CLEAN2",
  "C:\AAYS1_GITHUB_BRIDGE\chat_gpt_clone_1",
  "F:\AAYS_DATA",
  "F:\AAYS_DATA\sales_match_program"
)

$ImportantRelativePaths = @(
  ".git",
  "pyproject.toml",
  "requirements.txt",
  "package.json",
  "docker-compose.yml",
  "docker-compose.yaml",
  "app",
  "scripts",
  "docs",
  "data",
  "ai-tasks",
  "ai-heartbeat",
  "ai-runner-outputs"
)

$rootReports = @()
foreach ($root in $CandidateRoots) {
  $rootInfo = Get-ItemInfoSafe $root
  $relInfos = @()
  foreach ($rel in $ImportantRelativePaths) {
    $relInfos += Get-ItemInfoSafe (Join-Path $root $rel)
  }
  $rootReports += [ordered]@{
    root = $root
    info = $rootInfo
    top_level_names = Get-ChildNamesSafe $root 120
    important_paths = $relInfos
  }
}

$manifestHits = @()
foreach ($root in $CandidateRoots) {
  if (-not (Test-PathSafe $root)) { continue }
  try {
    $hits = Get-ChildItem -LiteralPath $root -Recurse -File -ErrorAction SilentlyContinue |
      Where-Object {
        $_.FullName -match "(?i)(handoff|manifest|source|sales|parcel|runner|current-task|last-task|quality|unmatched|build_report)" -and
        $_.Length -lt 20971520
      } |
      Select-Object -First 250 FullName, Length, LastWriteTime
    foreach ($hit in $hits) {
      $manifestHits += [ordered]@{
        path = $hit.FullName
        length_bytes = $hit.Length
        last_write_time = $hit.LastWriteTime.ToString("s")
      }
    }
  } catch {
    $manifestHits += [ordered]@{ path = $root; error = $_.Exception.Message }
  }
}

$secretVarNames = @("DATABASE_URL", "PGPASSWORD", "OPENAI_API_KEY", "GITHUB_TOKEN", "JWT_SECRET", "API_KEY")
$secretPresence = @{}
foreach ($name in $secretVarNames) {
  $secretPresence[$name] = [bool][Environment]::GetEnvironmentVariable($name)
}

$bridgeFiles = [ordered]@{
  runner_v4 = Get-ItemInfoSafe (Join-Path $BridgeRoot "ai-heartbeat\runner-v4.md")
  portable_runner = Get-ItemInfoSafe (Join-Path $BridgeRoot "ai-heartbeat\portable-runner.md")
  current_task = Get-ItemInfoSafe (Join-Path $BridgeRoot "ai-tasks\current-task.json")
  last_task_id = Get-ItemInfoSafe (Join-Path $BridgeRoot "ai-tasks\.last-task-id")
}

$result = [ordered]@{
  task_id = "parcelsales-001-discovery-root-and-manifest-20260518"
  task_namespace = "PARCELSALES"
  project_label = "uk-historical-sales-parcel-match"
  generated_at = (Get-Date).ToString("s")
  mode = "read_only_discovery_no_db_writes_no_raw_commands"
  bridge_root = $BridgeRoot
  output_dir = $OutDir
  candidate_roots = $rootReports
  manifest_hits = $manifestHits
  secret_presence_boolean_only = $secretPresence
  bridge_files = $bridgeFiles
  next_recommended_task = [ordered]@{
    id = "parcelsales-002-source-inventory-and-matching-design-20260518"
    purpose = "Use discovery output to identify official data sources, local project root, existing scripts, and safe matching plan."
    requires_user_or_chatgpt_review = $true
  }
}

$resultJson = Join-Path $OutDir "discovery_result.json"
$result | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $resultJson -Encoding UTF8

$reportPath = Join-Path $OutDir "discovery_report.md"
$lines = New-Object System.Collections.Generic.List[string]
$lines.Add("# PARCELSALES 001 Discovery Report")
$lines.Add("")
$lines.Add("Task: parcelsales-001-discovery-root-and-manifest-20260518")
$lines.Add("Mode: read-only discovery; no DB writes; no scoring promotion; no secret values printed.")
$lines.Add("")
$lines.Add("## Bridge")
$lines.Add("- Bridge root: $BridgeRoot")
$lines.Add("- Output dir: $OutDir")
$lines.Add("")
$lines.Add("## Candidate roots")
foreach ($r in $rootReports) {
  $exists = $r.info.exists
  $lines.Add("- $($r.root) exists=$exists")
}
$lines.Add("")
$lines.Add("## Manifest/source-like hits")
foreach ($m in ($manifestHits | Select-Object -First 80)) {
  if ($m.Contains("error")) { $lines.Add("- ERROR $($m.path): $($m.error)") }
  else { $lines.Add("- $($m.path) ($($m.length_bytes) bytes)") }
}
$lines.Add("")
$lines.Add("## Secret presence")
$lines.Add("Only boolean presence is reported; values are never printed.")
foreach ($name in $secretVarNames) { $lines.Add("- $name present=$($secretPresence[$name])") }
$lines.Add("")
$lines.Add("## Outputs")
$lines.Add("- discovery_result.json")
$lines.Add("- discovery_report.md")
$lines.Add("- next_task_plan.json")
$lines | Set-Content -LiteralPath $reportPath -Encoding UTF8

$nextPlan = [ordered]@{
  task_namespace = "PARCELSALES"
  project_label = "uk-historical-sales-parcel-match"
  proposed_next_task_id = "parcelsales-002-source-inventory-and-matching-design-20260518"
  proposed_script_path = "parcelsales_002_source_inventory_and_matching_design_20260518.ps1"
  required_review_inputs = @("discovery_result.json", "discovery_report.md")
  rules = @(
    "Official sources only for evidence-backed rows.",
    "No fabricated data.",
    "Every output row must have source/evidence fields.",
    "Do not write DB data in discovery phase."
  )
}
$nextPlan | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $OutDir "next_task_plan.json") -Encoding UTF8

Write-Host "PARCELSALES_DISCOVERY_OUTPUT=$OutDir"
Write-Host "PARCELSALES_DISCOVERY_RESULT=$resultJson"
Write-Host "PARCELSALES_DISCOVERY_REPORT=$reportPath"
