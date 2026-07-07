$ErrorActionPreference = 'Continue'

$TaskId = 'aays1-continue-046-to-044-20260708'
$PageKey = 'aays1'
$UtcNow = (Get-Date).ToUniversalTime().ToString('o')
$PageRoot = Resolve-Path (Join-Path $PSScriptRoot '..')
$RepoRoot = Resolve-Path (Join-Path $PageRoot '..\..\..')

$StatusDir = Join-Path $PageRoot 'status'
$ReportsDir = Join-Path $PageRoot 'reports'
$HeartbeatDir = Join-Path $PageRoot 'heartbeat'
$RunnerOutputsDir = Join-Path $PageRoot 'runner_outputs'
$QueueDir = Join-Path $PageRoot 'queue'
New-Item -ItemType Directory -Force -Path $StatusDir, $ReportsDir, $HeartbeatDir, $RunnerOutputsDir, $QueueDir | Out-Null

function Write-Utf8($Path, $Text) {
  $dir = Split-Path -Parent $Path
  if ($dir -and -not (Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
  [System.IO.File]::WriteAllText($Path, $Text, [System.Text.UTF8Encoding]::new($false))
}
function To-JsonText($Obj) { return ($Obj | ConvertTo-Json -Depth 12) }
function Test-LocalUrl($Url) {
  $ok = $false; $statusCode = $null; $err = $null
  try {
    $r = Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 6
    $statusCode = [int]$r.StatusCode
    $ok = ($statusCode -ge 200 -and $statusCode -lt 400)
  } catch { $err = $_.Exception.Message }
  return [ordered]@{ url = $Url; ok = $ok; status_code = $statusCode; error = $err }
}

$heartbeat = "checked_at=$UtcNow; page_key=$PageKey; task_id=$TaskId; state=running"
Write-Utf8 (Join-Path $HeartbeatDir 'aays1_continue_046_to_044_heartbeat_latest.txt') $heartbeat

$requiredEvidence = @(
  'docs/chatgpt_status/aays1/status/aays1_site_visible_current_status_latest.json',
  'docs/chatgpt_status/aays1/status/aays1_work_progress_latest.json',
  'docs/chatgpt_status/aays1/status/aays1_required_sources_latest.json',
  'docs/chatgpt_status/aays1/status/aays1_046_status_latest.json',
  'docs/chatgpt_status/aays1/status/046_recovery_latest.json',
  'docs/chatgpt_status/aays1/reports/046_recovery_report.md',
  'docs/chatgpt_status/aays1/status/preflight_latest.json',
  'docs/chatgpt_status/aays1/reports/preflight_report.md'
)
$evidence = @()
foreach ($rel in $requiredEvidence) {
  $full = Join-Path $RepoRoot $rel
  $evidence += [ordered]@{ path = $rel; exists = (Test-Path -LiteralPath $full) }
}

$watchdog = [ordered]@{
  page_key = $PageKey
  task_id = $TaskId
  checked_at = $UtcNow
  status = 'watchdog_checked'
  checked_files = $evidence
  missing_required_files = @($evidence | Where-Object { -not $_.exists } | ForEach-Object { $_.path })
  final_ready = $false
  fake_data = $false
}
Write-Utf8 (Join-Path $StatusDir 'watchdog_latest.json') (To-JsonText $watchdog)
Write-Utf8 (Join-Path $ReportsDir 'watchdog_report.md') ("# aays1 Watchdog Report`n`nchecked_at=$UtcNow`nmissing_required_files=" + (($watchdog.missing_required_files) -join ';') + "`nfinal_ready=false`n")

$endpointResults = @(
  Test-LocalUrl 'http://127.0.0.1:8010/england_map_web/',
  Test-LocalUrl 'http://127.0.0.1:8020/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html?refresh=20260630-final'
)
$endpointOk = (@($endpointResults | Where-Object { -not $_.ok }).Count -eq 0)
$endpointStatus = [ordered]@{
  page_key = $PageKey
  task_id = $TaskId
  checked_at = $UtcNow
  status = $(if ($endpointOk) { 'endpoint_health_ok' } else { 'endpoint_health_blocked_or_unavailable' })
  endpoint_ok = $endpointOk
  results = $endpointResults
  final_ready = $false
  fake_data = $false
}
Write-Utf8 (Join-Path $StatusDir 'endpoint_health_latest.json') (To-JsonText $endpointStatus)
Write-Utf8 (Join-Path $ReportsDir 'endpoint_health_report.md') ("# aays1 Endpoint Health Report`n`nchecked_at=$UtcNow`nendpoint_ok=$endpointOk`nfinal_ready=false`n")

$scanFiles = Get-ChildItem -LiteralPath $PageRoot -Recurse -File -ErrorAction SilentlyContinue | Where-Object { $_.FullName -match '\\(status|reports|queue|runner_outputs|heartbeat)\\' }
$flags = @()
foreach ($f in $scanFiles) {
  try {
    $txt = Get-Content -LiteralPath $f.FullName -Raw -ErrorAction Stop
    if ($txt -match 'final_ready\s*[:=]\s*true') { $flags += [ordered]@{ path = $f.FullName.Replace($RepoRoot.Path + '\',''); flag = 'final_ready_true_seen' } }
    if ($txt -match 'fake_data\s*[:=]\s*true') { $flags += [ordered]@{ path = $f.FullName.Replace($RepoRoot.Path + '\',''); flag = 'fake_data_true_seen' } }
  } catch {}
}
$redFlag = [ordered]@{
  page_key = $PageKey
  task_id = $TaskId
  checked_at = $UtcNow
  status = $(if ($flags.Count -eq 0) { 'red_flag_quickscan_clear' } else { 'red_flag_quickscan_flags_found' })
  flags = $flags
  final_ready = $false
  fake_data = $false
}
Write-Utf8 (Join-Path $StatusDir 'red_flag_quickscan_latest.json') (To-JsonText $redFlag)
Write-Utf8 (Join-Path $ReportsDir 'red_flag_quickscan_report.md') ("# aays1 Red Flag Quickscan Report`n`nchecked_at=$UtcNow`nflag_count=$($flags.Count)`nfinal_ready=false`n")

$childTaskPath = Join-Path $QueueDir 'aays1-044-accuracy-expansion-child-20260708.task.json'
$childTask = [ordered]@{
  task_id = 'aays1-044-accuracy-expansion-child-20260708'
  page_key = $PageKey
  status = 'queued'
  parent_task_id = $TaskId
  script_path = 'docs/chatgpt_status/aays1/automation/aays1_044_accuracy_expansion_child_20260708.ps1'
  expected_outputs = @(
    'docs/chatgpt_status/aays1/status/044_accuracy_expansion_latest.json',
    'docs/chatgpt_status/aays1/reports/044_accuracy_expansion_report.md',
    'docs/chatgpt_status/aays1/status/site_visible_score_status_latest.json'
  )
  final_ready = $false
  fake_data = $false
}
Write-Utf8 $childTaskPath (To-JsonText $childTask)

$summary = [ordered]@{
  page_key = $PageKey
  task_id = $TaskId
  checked_at = $UtcNow
  status = 'continue_step_done_child_044_queued'
  watchdog_status_path = 'docs/chatgpt_status/aays1/status/watchdog_latest.json'
  endpoint_health_status_path = 'docs/chatgpt_status/aays1/status/endpoint_health_latest.json'
  red_flag_status_path = 'docs/chatgpt_status/aays1/status/red_flag_quickscan_latest.json'
  child_044_task_path = 'docs/chatgpt_status/aays1/queue/aays1-044-accuracy-expansion-child-20260708.task.json'
  progress_percent = $(if ($endpointOk -and $flags.Count -eq 0) { 65 } else { 60 })
  final_ready = $false
  fake_data = $false
  next_action = 'single runner should pick up the queued 044 accuracy expansion child task'
}
Write-Utf8 (Join-Path $StatusDir 'aays1_continue_046_to_044_latest.json') (To-JsonText $summary)
Write-Utf8 (Join-Path $RunnerOutputsDir 'aays1_continue_046_to_044_20260708_runner_output.txt') (To-JsonText $summary)
Write-Output (To-JsonText $summary)
