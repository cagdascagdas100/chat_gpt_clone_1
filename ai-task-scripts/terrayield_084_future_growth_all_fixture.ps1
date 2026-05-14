[CmdletBinding()]
param(
  [string]$ProjectRoot = "C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence",
  [string]$BridgeRoot = "C:\AAYS1_GITHUB_BRIDGE\chat_gpt_clone_1",
  [string]$Mode = "fixture",
  [int]$Limit = 300,
  [string]$ApiBaseUrl = "http://127.0.0.1:8010"
)

$ErrorActionPreference = "Stop"

function Write-AuditJson {
  param(
    [string]$Path,
    [hashtable]$Payload
  )
  $dir = Split-Path -Parent $Path
  if (-not (Test-Path -LiteralPath $dir)) {
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
  }
  ($Payload | ConvertTo-Json -Depth 10) | Out-File -FilePath $Path -Encoding UTF8
}

$startedAt = (Get-Date).ToUniversalTime().ToString("s") + "Z"
$auditPath = Join-Path $BridgeRoot "ai-results\terrayield-084-future-growth-all-fixture.audit.json"
$taskStatus = "failed"
$nextAction = "Inspect logs and rerun future growth fixture task."
$jobExitCode = 1
$smokeExitCode = 1
$jobJson = $null
$smokeJson = $null
$errors = @()

function To-IntOrZero {
  param([object]$Value)
  if ($null -eq $Value) { return 0 }
  try { return [int]$Value } catch { return 0 }
}

try {
  Set-Location $ProjectRoot

  $jobOutput = & python -m app.future_growth.cli "future-growth:all" --mode $Mode --limit $Limit 2>&1
  $jobExitCode = $LASTEXITCODE
  $jobText = ($jobOutput | Out-String).Trim()
  if ($jobText) {
    try {
      $jobJson = $jobText | ConvertFrom-Json -ErrorAction Stop
    } catch {
      $errors += "job_json_parse_failed"
    }
  }
  if ($jobExitCode -ne 0) {
    throw "future_growth_job_failed"
  }

  $smokeOutput = & python scripts\future_growth_frontend_smoke.py --base-url $ApiBaseUrl --limit 5 2>&1
  $smokeExitCode = $LASTEXITCODE
  $smokeText = ($smokeOutput | Out-String).Trim()
  if ($smokeText) {
    try {
      $smokeJson = $smokeText | ConvertFrom-Json -ErrorAction Stop
    } catch {
      $errors += "smoke_json_parse_failed"
    }
  }

  if ($smokeExitCode -ne 0) {
    throw "future_growth_smoke_failed"
  }

  $taskStatus = "completed"
  $nextAction = "Future Growth fixture pipeline is healthy. Keep runner schedule active."
} catch {
  if (-not $errors) {
    $errors += "task_failed"
  }
}

$finishedAt = (Get-Date).ToUniversalTime().ToString("s") + "Z"
$jobCounts = @{}
if ($jobJson) {
  if ($jobJson.ingest) {
    $jobCounts["ingest_loaded"] = To-IntOrZero $jobJson.ingest.loaded_total
  }
  if ($jobJson.score) {
    $jobCounts["scored_parcels"] = To-IntOrZero $jobJson.score.processed
  }
  if ($jobJson.vectors) {
    $jobCounts["vector_rows"] = To-IntOrZero $jobJson.vectors.upserted
  }
}

$smokeSummary = @{}
if ($smokeJson) {
  $smokeSummary["status"] = [string]$smokeJson.status
  $smokeSummary["checked_parcel_id"] = $smokeJson.checked_parcel_id
  $smokeSummary["layer_feature_count"] = $smokeJson.checks.layer_feature_count
  $smokeSummary["popup_evidence_scoped_to_parcel"] = [bool]$smokeJson.checks.popup_evidence_scoped_to_parcel
  $smokeSummary["methodology_disclaimer_present"] = [bool]$smokeJson.checks.methodology_disclaimer_present
}

$audit = @{
  id = "terrayield-084-future-growth-all-fixture"
  status = $taskStatus
  mode = $Mode
  limit = $Limit
  project_root = $ProjectRoot
  bridge_root = $BridgeRoot
  api_base_url = $ApiBaseUrl
  started_at = $startedAt
  finished_at = $finishedAt
  future_growth_job_ok = ($jobExitCode -eq 0)
  future_growth_smoke_ok = ($smokeExitCode -eq 0)
  job_exit_code = $jobExitCode
  smoke_exit_code = $smokeExitCode
  job_counts = $jobCounts
  smoke_summary = $smokeSummary
  errors = $errors
  next_action = $nextAction
}

Write-AuditJson -Path $auditPath -Payload $audit
Write-Output "audit_path=$auditPath"
Write-Output "status=$taskStatus"
Write-Output "future_growth_job_ok=$($jobExitCode -eq 0)"
Write-Output "future_growth_smoke_ok=$($smokeExitCode -eq 0)"
Write-Output "next_action=$nextAction"

if ($taskStatus -ne "completed") {
  exit 1
}
