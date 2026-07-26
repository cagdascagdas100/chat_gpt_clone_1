$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$RepoRoot = "F:\chatgpt\chat_gpt_clone_1_main"
$PageKey = "distance_property_types"
$Now = Get-Date -Format "yyyyMMdd_HHmmss"

$StatusRoot = Join-Path $RepoRoot "docs\chatgpt_status\$PageKey"
$QueueDir = Join-Path $StatusRoot "queue"
$ReportsDir = Join-Path $StatusRoot "reports"
$OutputsDir = Join-Path $StatusRoot "runner_outputs"
$InputsDir = Join-Path $StatusRoot "inputs"

foreach ($d in @($StatusRoot,$QueueDir,$ReportsDir,$OutputsDir,$InputsDir)) {
  New-Item -ItemType Directory -Force -Path $d | Out-Null
}

$ReportPath = Join-Path $OutputsDir "fix_runner_git_sync_$Now.report.json"
$ProgressPath = Join-Path $ReportsDir "distance_property_types_progress_latest.md"

Push-Location $RepoRoot

try {
  git rev-parse --is-inside-work-tree | Out-Null

  $BackupBranch = "backup/local-main-before-runner-fix-$Now"
  $CurrentHead = (git rev-parse HEAD).Trim()
  git branch $BackupBranch $CurrentHead

  $ExcludePath = Join-Path $RepoRoot ".git\info\exclude"
  @"

# local-only excludes for AAYS runner repair
terrayield_land_intelligence/.venv/
**/.venv/
__pycache__/
*.pyc
"@ | Add-Content -LiteralPath $ExcludePath -Encoding UTF8

  git fetch origin main
  git checkout main
  git reset --hard origin/main

  foreach ($d in @($StatusRoot,$QueueDir,$ReportsDir,$OutputsDir,$InputsDir)) {
    New-Item -ItemType Directory -Force -Path $d | Out-Null
  }

  $TemplatePath = Join-Path $InputsDir "distance_property_types_source_candidates_TEMPLATE.csv"
  if (-not (Test-Path -LiteralPath $TemplatePath)) {
    "parcel_id,geometry_wkt,centroid_lat,centroid_lon,candidate_property_type,official_source_evidence,web_source_evidence,map_source_evidence,photo_ai_evidence,photo_ai_image_path,photo_ai_model_or_tool,photo_ai_observation,source_date,matching_method,nearest_industrial_unit_distance_m,nearest_detached_home_distance_m,nearest_retail_property_distance_m,nearest_apartment_building_distance_m,nearest_office_building_distance_m,nearest_mixed_building_distance_m,notes" |
      Set-Content -LiteralPath $TemplatePath -Encoding UTF8
  }

  $BridgeRoot = $null
  foreach ($b in @("C:\AAYS_GITHUB_BRIDGE_CLEAN2","F:\AAYS_GITHUB_BRIDGE_CLEAN2")) {
    if (Test-Path -LiteralPath $b) { $BridgeRoot = $b; break }
  }

  $LivePending = $null
  $Copied = 0
  if ($BridgeRoot) {
    $LivePending = Join-Path $BridgeRoot "ai-queue\pending"
    New-Item -ItemType Directory -Force -Path $LivePending | Out-Null

    Get-ChildItem -LiteralPath $QueueDir -Filter "*.task.json" -File -ErrorAction SilentlyContinue | ForEach-Object {
      Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $LivePending $_.Name) -Force
      $Copied++
    }
  }

  $RunnerCandidates = @()
  foreach ($root in @($BridgeRoot,$RepoRoot,"C:\Users\cagda\Documents\GitHub\AAYS") | Where-Object { $_ -and (Test-Path -LiteralPath $_) }) {
    $RunnerCandidates += Get-ChildItem -LiteralPath $root -Recurse -File -Filter "*.ps1" -ErrorAction SilentlyContinue |
      Where-Object { $_.Name -match "RUN_SINGLE|runner|queue|MULTI_PAGE|single" -or $_.FullName -match "RUN_SINGLE|runner|queue|MULTI_PAGE|single" }
  }

  $SelectedRunner = $null
  if ($RunnerCandidates.Count -gt 0) {
    $SelectedRunner = ($RunnerCandidates | Sort-Object FullName | Select-Object -First 1).FullName
  }

  $RunnerProcesses = @(Get-CimInstance Win32_Process | Where-Object {
    $_.Name -match "powershell|pwsh" -and (
      $_.CommandLine -match "RUN_SINGLE" -or
      $_.CommandLine -match "runner" -or
      $_.CommandLine -match "ai-queue" -or
      $_.CommandLine -match "distance_property_types"
    )
  })

  $Report = [ordered]@{
    task_id = "distance_property_types_fix_runner_git_sync_$Now"
    page_key = $PageKey
    timestamp_local = (Get-Date).ToString("s")
    repo_root = $RepoRoot
    bridge_root = $BridgeRoot
    live_pending = $LivePending
    backup_branch = $BackupBranch
    local_main_reset_to_origin_main = $true
    queue_files_copied = $Copied
    selected_runner = $SelectedRunner
    runner_already_running = ($RunnerProcesses.Count -gt 0)
    runner_process_count = $RunnerProcesses.Count
    final_ready = $false
    safety = @{
      fake_data = $false
      db_write = $false
      ddl = $false
      migration = $false
      production_deploy = $false
    }
  }

  $Report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $ReportPath -Encoding UTF8

@"
# Distance Property Types - Progress Latest

page_key=$PageKey
task_id=distance_property_types_fix_runner_git_sync_$Now
run_finished_at=$((Get-Date).ToString("s"))
status=LOCAL_GIT_SYNC_FIXED_RUNNER_PICKUP_READY
completion_percent=20
final_ready=false
chatgpt_continue_mode=true
continue_command=devam et
latest_runner_fix_report=docs/chatgpt_status/$PageKey/runner_outputs/$(Split-Path $ReportPath -Leaf)

## Local repair result

- local main reset to origin/main
- backup branch: $BackupBranch
- queue files copied: $Copied
- selected runner: $SelectedRunner
- runner already running: $($RunnerProcesses.Count -gt 0)

## Safety flags

fake_data=false
db_write=false
ddl=false
migration_apply=false
prod_deploy=false

## Next action

Say devam et in ChatGPT.
"@ | Set-Content -LiteralPath $ProgressPath -Encoding UTF8

  git add "docs/chatgpt_status/$PageKey"
  if (git status --porcelain) {
    git commit -m "Fix distance property types local runner git sync"
    git pull --rebase origin main
    git push origin main
  }

  if ($RunnerProcesses.Count -gt 0) {
    Write-Host "Runner already running. Not starting another runner." -ForegroundColor Green
  }
  elseif ($SelectedRunner) {
    Write-Host "Starting runner: $SelectedRunner" -ForegroundColor Green
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $SelectedRunner
  }
  else {
    Write-Host "No runner script found. Report pushed if git succeeded." -ForegroundColor Yellow
  }
}
finally {
  Pop-Location
}
