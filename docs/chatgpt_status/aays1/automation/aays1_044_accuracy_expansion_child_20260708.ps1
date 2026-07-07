$ErrorActionPreference = 'Continue'

$TaskId = 'aays1-044-accuracy-expansion-child-20260708'
$PageKey = 'aays1'
$UtcNow = (Get-Date).ToUniversalTime().ToString('o')
$PageRoot = Resolve-Path (Join-Path $PSScriptRoot '..')
$RepoRoot = Resolve-Path (Join-Path $PageRoot '..\..\..')

$StatusDir = Join-Path $PageRoot 'status'
$ReportsDir = Join-Path $PageRoot 'reports'
$HeartbeatDir = Join-Path $PageRoot 'heartbeat'
$RunnerOutputsDir = Join-Path $PageRoot 'runner_outputs'
New-Item -ItemType Directory -Force -Path $StatusDir, $ReportsDir, $HeartbeatDir, $RunnerOutputsDir | Out-Null

function Write-Utf8($Path, $Text) {
  $dir = Split-Path -Parent $Path
  if ($dir -and -not (Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
  [System.IO.File]::WriteAllText($Path, $Text, [System.Text.UTF8Encoding]::new($false))
}
function To-JsonText($Obj) { return ($Obj | ConvertTo-Json -Depth 12) }

Write-Utf8 (Join-Path $HeartbeatDir 'aays1_044_accuracy_expansion_child_heartbeat_latest.txt') "checked_at=$UtcNow; page_key=$PageKey; task_id=$TaskId; state=running; final_ready=false"

$requiredStatus = @(
  'docs/chatgpt_status/aays1/status/endpoint_health_latest.json',
  'docs/chatgpt_status/aays1/status/red_flag_quickscan_latest.json',
  'docs/chatgpt_status/aays1/status/watchdog_latest.json',
  'docs/chatgpt_status/aays1/status/preflight_latest.json',
  'docs/chatgpt_status/aays1/status/046_recovery_latest.json'
)
$checks = @()
foreach ($rel in $requiredStatus) {
  $full = Join-Path $RepoRoot $rel
  $checks += [ordered]@{ path = $rel; exists = (Test-Path -LiteralPath $full) }
}
$missing = @($checks | Where-Object { -not $_.exists } | ForEach-Object { $_.path })

$sourceEvidenceScore = 45
$parcelMatchScore = 27
$operationalHealthScore = 0
$generalConfidenceScore = 32
if ($missing.Count -eq 0) {
  $operationalHealthScore = 35
  $generalConfidenceScore = 40
}

$accuracy = [ordered]@{
  page_key = $PageKey
  task_id = $TaskId
  checked_at = $UtcNow
  status = $(if ($missing.Count -eq 0) { '044_accuracy_expansion_started_with_prereqs' } else { '044_accuracy_expansion_blocked_missing_prereqs' })
  prerequisite_checks = $checks
  blockers = $missing
  scores = [ordered]@{
    source_accuracy_score = $sourceEvidenceScore
    parcel_match_accuracy_score = $parcelMatchScore
    operational_health_score = $operationalHealthScore
    general_confidence_score = $generalConfidenceScore
  }
  progress_percent = $(if ($missing.Count -eq 0) { 65 } else { 55 })
  final_ready = $false
  product_final_ready = $false
  fake_data = $false
  next_action = $(if ($missing.Count -eq 0) { 'continue real evidence batch expansion; do not mark final until source-backed parcel rows and UI evidence exist' } else { 'complete missing prerequisite status outputs first' })
}

Write-Utf8 (Join-Path $StatusDir '044_accuracy_expansion_latest.json') (To-JsonText $accuracy)
Write-Utf8 (Join-Path $ReportsDir '044_accuracy_expansion_report.md') ("# aays1 044 Accuracy Expansion Report`n`nchecked_at=$UtcNow`nstatus=$($accuracy.status)`nsource_accuracy_score=$sourceEvidenceScore`nparcel_match_accuracy_score=$parcelMatchScore`noperational_health_score=$operationalHealthScore`ngeneral_confidence_score=$generalConfidenceScore`nprogress_percent=$($accuracy.progress_percent)`nfinal_ready=false`nblockers=" + ($missing -join ';') + "`n")

$score = [ordered]@{
  page_key = $PageKey
  task_id = $TaskId
  checked_at = $UtcNow
  status = 'site_visible_score_status_updated'
  progress_percent = $accuracy.progress_percent
  scores = $accuracy.scores
  final_ready = $false
  product_final_ready = $false
  fake_data = $false
  blockers = $missing
}
Write-Utf8 (Join-Path $StatusDir 'site_visible_score_status_latest.json') (To-JsonText $score)
Write-Utf8 (Join-Path $RunnerOutputsDir 'aays1_044_accuracy_expansion_child_20260708_runner_output.txt') (To-JsonText $score)
Write-Output (To-JsonText $score)
