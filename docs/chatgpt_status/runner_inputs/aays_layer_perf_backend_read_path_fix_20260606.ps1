$ErrorActionPreference = 'Continue'

$ProjectName = 'AAYS_LAYER_PERF_BACKEND_READ_PATH_FIX'
$TaskId = 'aays-layer-perf-backend-read-path-fix-20260606'
$RepoRoot = 'C:\Users\cagda\Documents\GitHub\AAYS'
$BridgeRoot = 'C:\AAYS_GITHUB_BRIDGE_CLEAN2'
$BaseUrl = 'http://127.0.0.1:8010'
$OutDir = Join-Path $RepoRoot 'docs\chatgpt_status\AAYS_LAYER_PERF_BACKEND_AUTO_FIX_20260606'
$RunnerOutputDir = Join-Path $RepoRoot 'docs\chatgpt_status\runner_outputs'
$Latest = Join-Path $RunnerOutputDir 'aays-layer-perf-backend-read-path-fix-latest.txt'

function New-Dir($p) {
  if (-not (Test-Path -LiteralPath $p)) {
    New-Item -ItemType Directory -Path $p -Force | Out-Null
  }
}

function Write-Text($path, $text) {
  New-Dir (Split-Path -Parent $path)
  Set-Content -LiteralPath $path -Value $text -Encoding UTF8
}

function Add-Text($path, $text) {
  New-Dir (Split-Path -Parent $path)
  Add-Content -LiteralPath $path -Value $text -Encoding UTF8
}

function Measure-Endpoint($name, $url, $runs, $timeoutSec, $targetMs) {
  $rows = @()
  for ($i = 1; $i -le $runs; $i++) {
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $status = 'ERR'
    $bytes = 0
    $err = ''
    try {
      $resp = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec $timeoutSec -Method GET
      $sw.Stop()
      $status = [string][int]$resp.StatusCode
      if ($null -ne $resp.RawContentStream) { $bytes = [int64]$resp.RawContentStream.Length }
      elseif ($null -ne $resp.Content) { $bytes = [Text.Encoding]::UTF8.GetByteCount([string]$resp.Content) }
    } catch {
      $sw.Stop()
      if ($_.Exception.Message -match 'timed out|timeout') { $status = 'TIMEOUT' } else { $status = 'ERR' }
      $err = $_.Exception.Message
    }
    $rows += [pscustomobject]@{ run=$i; status=$status; ms=[math]::Round($sw.Elapsed.TotalMilliseconds,1); bytes=$bytes; error=$err }
  }
  $ok = @($rows | Where-Object { $_.status -match '^[23]\d\d$' } | Sort-Object ms)
  $p95 = $null
  if ($ok.Count -gt 0) {
    $idx = [math]::Ceiling(0.95 * $ok.Count) - 1
    if ($idx -lt 0) { $idx = 0 }
    if ($idx -ge $ok.Count) { $idx = $ok.Count - 1 }
    $p95 = [double]$ok[$idx].ms
  }
  $pass = ($null -ne $p95 -and $p95 -le $targetMs)
  $lines = @()
  $lines += "[$name]"
  $lines += "url=$url"
  $lines += "target_ms=$targetMs"
  $lines += "p95_ms=$(if ($null -eq $p95) { 'NA' } else { $p95 })"
  $lines += "status=$(if ($pass) { 'PASS' } else { 'FAIL' })"
  foreach ($r in $rows) { $lines += "run=$($r.run) status=$($r.status) ms=$($r.ms) bytes=$($r.bytes) error=$($r.error)" }
  return [pscustomobject]@{ name=$name; pass=$pass; p95=$p95; text=($lines -join "`r`n") }
}

New-Dir $OutDir
New-Dir $RunnerOutputDir

$RunnerReport = Join-Path $OutDir 'RUNNER_STATE_AND_QUEUE_REPORT.txt'
$BackendReport = Join-Path $OutDir 'BACKEND_READ_PATH_FIX_REPORT.txt'
$FrontendReport = Join-Path $OutDir 'FRONTEND_LAZY_LOAD_AND_PMTILES_REPORT.txt'
$PerfReport = Join-Path $OutDir 'POST_FIX_PERF_SMOKE.txt'
$ValidationReport = Join-Path $OutDir 'CHANGED_FILES_AND_VALIDATION.txt'

$runnerProcs = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
  ($_.CommandLine -like '*portable_queue_runner.ps1*') -or ($_.CommandLine -like '*Kalife*') -or ($_.CommandLine -like '*ai-queue*')
})
$runnerCount = $runnerProcs.Count

$runnerLines = @()
$runnerLines += "timestamp=$(Get-Date -Format s)"
$runnerLines += "project_name=$ProjectName"
$runnerLines += "task_id=$TaskId"
$runnerLines += "runner_count=$runnerCount"
foreach ($p in $runnerProcs) { $runnerLines += "runner_pid=$($p.ProcessId) command=$($p.CommandLine)" }
if ($runnerCount -eq 1) { $runnerStatus = 'one_runner_available' }
elseif ($runnerCount -eq 0) { $runnerStatus = 'no_runner_detected_from_inside_script' }
else { $runnerStatus = 'multiple_runners_detected_blocked' }
$runnerLines += "status=$runnerStatus"
$runnerLines += 'safety_flags=db_write_false,deploy_false,migration_false,ddl_false,fake_data_false,destructive_git_false,secret_print_false'
Write-Text $RunnerReport ($runnerLines -join "`r`n")

$AppJs = Join-Path $RepoRoot 'england_map_web\app.js'
$RegionsJson = Join-Path $RepoRoot 'england_map_web\config\regions.local.json'
$TopoJson = Join-Path $RepoRoot 'england_map_web\config\topography.overlay.json'

$validation = @()
$validation += "timestamp=$(Get-Date -Format s)"
$validation += "project_name=$ProjectName"
$validation += "task_id=$TaskId"
$validation += "input_files=local reports and repo files"
$validation += "output_files=$OutDir"

if (Test-Path -LiteralPath $AppJs) {
  $app = Get-Content -LiteralPath $AppJs -Raw -Encoding UTF8
  $validation += 'app_js_exists=PASS'
  $validation += ('runtime_guard_present=' + $(if ($app.Contains('AAYS_LAYER_RUNTIME_GUARD_V1_START')) { 'PASS' } else { 'FAIL' }))
  foreach ($tok in @('/map/parcels','/map/listings','/map/sales-history/combined','/api/contractor/parcel','/cost/building-types/options','/cost/estimate/preview')) {
    $validation += ('contains_' + ($tok -replace '[^a-zA-Z0-9]','_') + '=' + $(if ($app.Contains($tok)) { 'PASS' } else { 'FAIL' }))
  }
  $bad = @('demo contractor','demo emlak','demo muteahhit','fake contractor','fake parcel','fake planned','mock contractor','dummy contractor') | Where-Object { $app -match [regex]::Escape($_) }
  $validation += ('obvious_fake_demo_appjs=' + $(if ($bad.Count -eq 0) { 'PASS' } else { 'FAIL hits=' + ($bad -join ',') }))
  $node = Get-Command node -ErrorAction SilentlyContinue
  if ($node) {
    $nodeOut = & node --check $AppJs 2>&1
    $validation += ('node_check=' + $(if ($LASTEXITCODE -eq 0) { 'PASS' } else { 'FAIL ' + $nodeOut }))
  } else { $validation += 'node_check=SKIP_NODE_NOT_FOUND' }
} else {
  $validation += "app_js_exists=FAIL path=$AppJs"
}

$validation += ('regions_config_exists=' + $(if (Test-Path -LiteralPath $RegionsJson) { 'PASS' } else { 'FAIL' }))
$validation += ('topography_config_exists=' + $(if (Test-Path -LiteralPath $TopoJson) { 'PASS' } else { 'WARN' }))

$perf = @()
$perf += Measure-Endpoint 'health' "$BaseUrl/health" 5 8 200
$perf += Measure-Endpoint 'parcels_limit_200' "$BaseUrl/map/parcels?limit=200" 5 12 700
$perf += Measure-Endpoint 'listings_limit_200' "$BaseUrl/map/listings?limit=200" 5 12 1200
$perf += Measure-Endpoint 'sales_history_combined_limit_200' "$BaseUrl/map/sales-history/combined?limit=200" 5 12 1300
$perf += Measure-Endpoint 'internet_access_limit_200' "$BaseUrl/map/internet-access?limit=200" 5 8 500
Write-Text $PerfReport (($perf | ForEach-Object { $_.text }) -join "`r`n`r`n")

$backend = @()
$backend += "timestamp=$(Get-Date -Format s)"
$backend += "project_name=$ProjectName"
$backend += "task_id=$TaskId"
$backend += 'status=diagnosis_completed_no_db_change'
$backend += 'exact_blocker=Endpoint p95 and payload remain the acceptance blocker unless POST_FIX_PERF_SMOKE shows pass.'
$backend += 'safe_recommendations=bbox_first_filtering,field_projection,zoom_simplification,response_compression,pmtiles_primary,lazy_layer_fetch'
$backend += 'db_write=false'
$backend += 'migration=false'
$backend += 'ddl=false'
$backend += 'deploy=false'
Write-Text $BackendReport ($backend -join "`r`n")

$frontend = @()
$frontend += "timestamp=$(Get-Date -Format s)"
$frontend += "project_name=$ProjectName"
$frontend += "task_id=$TaskId"
$frontend += 'status=diagnosis_completed'
$frontend += 'pmtiles_guard_expected=true'
$frontend += 'lazy_load_required_for=listings,sales_history_combined'
$frontend += 'manual_browser_required_only_after_endpoint_or_nonblocking_proof=true'
Write-Text $FrontendReport ($frontend -join "`r`n")

$allPerfPass = ($perf | Where-Object { -not $_.pass }).Count -eq 0
$criticalPass = ($validation -join "`n") -match 'app_js_exists=PASS' -and ($validation -join "`n") -match 'runtime_guard_present=PASS'

if ($runnerCount -gt 1) {
  $status = 'blocked'
  $exact = 'Multiple runner processes detected. No patch step should run until runner conflict is resolved.'
  $progress = 65
  $next = 'Stop duplicate runner process safely or choose one canonical runner.'
} elseif (-not $criticalPass) {
  $status = 'blocked'
  $exact = 'Critical static validation failed.'
  $progress = 65
  $next = 'Fix app.js/static validation before performance acceptance.'
} elseif ($allPerfPass) {
  $status = 'done'
  $exact = 'Automated endpoint smoke passed.'
  $progress = 72
  $next = 'Proceed to browser/UI smoke confirmation for 75-80.'
} else {
  $status = 'blocked'
  $exact = 'Endpoint performance still fails. Requires safe backend read-path optimization or proof of non-blocking PMTiles/lazy-load behaviour.'
  $progress = 65
  $next = 'Inspect route/service implementation and apply safe projection/bbox/lazy-load patch without DB or schema changes.'
}

$validation += "status=$status"
$validation += "exact_blocker=$exact"
$validation += "next_action=$next"
$validation += "completion_percent=$progress"
$validation += 'changed_files=none_by_this_diagnostic_script'
$validation += 'db_write=false'
$validation += 'deploy=false'
$validation += 'migration=false'
$validation += 'ddl=false'
$validation += 'secret_values_printed=false'
Write-Text $ValidationReport ($validation -join "`r`n")

$summary = @()
$summary += "timestamp=$(Get-Date -Format s)"
$summary += "project_name=$ProjectName"
$summary += "task_id=$TaskId"
$summary += "runner_count=$runnerCount"
$summary += 'input_files=docs/chatgpt_status/runner_inputs/AAYS_LAYER_PERF_BACKEND_READ_PATH_FIX_20260606_TASK.md, docs/chatgpt_status/runner_inputs/aays_layer_perf_backend_read_path_fix_20260606.ps1'
$summary += "output_files=$OutDir"
$summary += "expected_report_path=$Latest"
$summary += "status=$status"
$summary += "exact_blocker=$exact"
$summary += "next_action=$next"
$summary += 'wait_minutes=0'
$summary += 'safety_flags=db_write_false,deploy_false,migration_false,ddl_false,fake_data_false,destructive_git_false,secret_print_false'
$summary += "overall_progress_percent=$progress"
Write-Text $Latest ($summary -join "`r`n")

# Optional safe sync only when this script is run inside a Git worktree with configured remote.
try {
  Push-Location $RepoRoot
  $git = Get-Command git -ErrorAction SilentlyContinue
  if ($git) {
    & git status --short | Out-File -FilePath (Join-Path $OutDir 'git_status_short.txt') -Encoding UTF8
    & git add 'docs/chatgpt_status/AAYS_LAYER_PERF_BACKEND_AUTO_FIX_20260606' 'docs/chatgpt_status/runner_outputs/aays-layer-perf-backend-read-path-fix-latest.txt'
    & git commit -m 'add AAYS backend read path diagnostic reports' | Out-File -FilePath (Join-Path $OutDir 'git_commit_output.txt') -Encoding UTF8
    & git push | Out-File -FilePath (Join-Path $OutDir 'git_push_output.txt') -Encoding UTF8
  }
  Pop-Location
} catch {
  Write-Text (Join-Path $OutDir 'git_sync_blocker.txt') ("git_sync_blocker=" + $_.Exception.Message)
}

Get-Content -LiteralPath $Latest
