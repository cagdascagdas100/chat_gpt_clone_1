param(
  [string]$RepoRoot = $env:AAYS_REPO_ROOT
)

$ErrorActionPreference = 'Continue'
if ([string]::IsNullOrWhiteSpace($RepoRoot)) { $RepoRoot = (Get-Location).Path }
$RepoRoot = [System.IO.Path]::GetFullPath($RepoRoot)
if (-not $RepoRoot.StartsWith('F:\', [System.StringComparison]::OrdinalIgnoreCase)) { throw "BLOCKED_WRONG_REPO_ROOT: $RepoRoot" }
Set-Location -LiteralPath $RepoRoot

$page = if ($env:AAYS_PAGE_KEY) { $env:AAYS_PAGE_KEY } else { 'topography' }
$taskId = if ($env:AAYS_TASK_ID) { $env:AAYS_TASK_ID } else { 'topography-verified-rows-resolution-20260704' }

function Ensure-Dir([string]$Path) { if ($Path -and -not (Test-Path -LiteralPath $Path)) { New-Item -ItemType Directory -Force -Path $Path | Out-Null } }
function Write-Utf8([string]$Path, [string]$Text) { Ensure-Dir (Split-Path -Parent $Path); [System.IO.File]::WriteAllText($Path, $Text, [System.Text.UTF8Encoding]::new($false)) }
function To-Json([object]$Obj) { $Obj | ConvertTo-Json -Depth 20 }
function Count-VerifiedRows([string]$CsvPath) {
  if (-not (Test-Path -LiteralPath $CsvPath)) { return 0 }
  $lines = @(Get-Content -LiteralPath $CsvPath | Where-Object { $_.Trim() })
  if ($lines.Count -le 1) { return 0 }
  return ($lines.Count - 1)
}

$statusDir = "docs/chatgpt_status/$page/status"
$reportDir = "docs/chatgpt_status/$page/reports"
$heartbeatDir = "docs/chatgpt_status/$page/heartbeat"
Ensure-Dir $statusDir
Ensure-Dir $reportDir
Ensure-Dir $heartbeatDir

$resolver = 'docs/chatgpt_status/topography/automation/RESOLVE_TOPOGRAPHY_VERIFIED_ROWS_BLOCKER_20260704.ps1'
$bridge = 'docs/chatgpt_status/topography/automation/topography_single_runner_bridge_20260703.ps1'
$csv = 'docs/chatgpt_status/topography/fixtures/topography_verified_rows_template_20260703.csv'
$latest = 'outputs/england_program_parcel_matrix_20260629/topography_updates/latest_changes.json'
$smoke = 'docs/chatgpt_status/topography/browser_smoke/topography_browser_smoke_latest_20260704.json'
$gatePath = "docs/chatgpt_status/$page/status/${taskId}_gate.json"
$entryReportPath = "docs/chatgpt_status/$page/reports/${taskId}_entry_report.json"
$hbPath = "docs/chatgpt_status/$page/heartbeat/${taskId}_entry_heartbeat.txt"

$automationOutput = ''
$automationExit = 0
if (Test-Path -LiteralPath $resolver) {
  $out = & powershell -NoProfile -ExecutionPolicy Bypass -File $resolver -RepoRoot $RepoRoot 2>&1
  $automationExit = $LASTEXITCODE
  $automationOutput = ($out | Out-String)
} elseif (Test-Path -LiteralPath $bridge) {
  $out = & powershell -NoProfile -ExecutionPolicy Bypass -File $bridge -RepoRoot $RepoRoot 2>&1
  $automationExit = $LASTEXITCODE
  $automationOutput = ($out | Out-String)
} else {
  $automationExit = 99
  $automationOutput = 'missing resolver and bridge scripts'
}

$filled = Count-VerifiedRows $csv
$latestFilled = $null
$latestFinal = $false
if (Test-Path -LiteralPath $latest) {
  try {
    $j = Get-Content -LiteralPath $latest -Raw | ConvertFrom-Json
    if ($j.summary -and $null -ne $j.summary.filled_parcel_count) { $latestFilled = [int]$j.summary.filled_parcel_count }
    if ($null -ne $j.final_ready) { $latestFinal = [bool]$j.final_ready }
  } catch {}
}
if ($latestFilled -ne $null) { $filled = [Math]::Max($filled, $latestFilled) }

$smokeOk = $false
if (Test-Path -LiteralPath $smoke) {
  try { $s = Get-Content -LiteralPath $smoke -Raw | ConvertFrom-Json; $smokeOk = [bool]$s.overall_ok } catch {}
}

$blockers = @()
if ($filled -le 0) { $blockers += 'verified_rows_missing' }
if (-not $smokeOk) { $blockers += 'browser_smoke_missing_or_not_current' }
if ($automationExit -ne 0 -and $filled -le 0) { $blockers += 'verified_rows_resolver_no_rows' }
elseif ($automationExit -ne 0) { $blockers += 'automation_exit_nonzero' }

$sourceRowGate = ($filled -gt 0)
$uiTokenGate = ($sourceRowGate -and $smokeOk)
$manualReview = -not ($sourceRowGate -and $uiTokenGate -and $latestFinal)
$finalReady = ($sourceRowGate -and $uiTokenGate -and $latestFinal -and $blockers.Count -eq 0)

$gate = [ordered]@{
  task_id = $taskId
  page_key = $page
  generated_at = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
  source_row_gate_passed = $sourceRowGate
  ui_token_gate_passed = $uiTokenGate
  browser_smoke_passed = $smokeOk
  post_sync_ok = $false
  manual_review_required = $manualReview
  fake_data = $false
  final_ready = $finalReady
  filled_parcel_count = $filled
  blockers = $blockers
}
Write-Utf8 $gatePath (To-Json $gate)

$entryReport = [ordered]@{
  task_id = $taskId
  page_key = $page
  runner_entry = 'topography_verified_rows_shared_runner_entry_20260705'
  resolver_exit_code = $automationExit
  filled_parcel_count = $filled
  source_row_gate_passed = $sourceRowGate
  ui_token_gate_passed = $uiTokenGate
  browser_smoke_passed = $smokeOk
  final_ready = $finalReady
  blockers = $blockers
  output_tail = (($automationOutput -split "`r?`n") | Select-Object -Last 40) -join "`n"
}
Write-Utf8 $entryReportPath (To-Json $entryReport)
Write-Utf8 $hbPath "TASK_ID=$taskId`nPAGE_KEY=$page`nSTATUS=entry_complete`nFINAL_READY=$finalReady`nFILLED_PARCEL_COUNT=$filled`nHEARTBEAT_AT=$((Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ'))`n"

# Important: return 0 so shared runner can commit/push controlled blocker reports. The gate carries final readiness.
exit 0
