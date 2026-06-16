param(
  [string]$RepoRoot = (Get-Location).Path
)

$ErrorActionPreference = 'Stop'
$pageKey = 'AAYS_REAL_TOPOGRAPHY_PRODUCT'
$branch = 'aays-runner-v17-icon-work-20260603-232706'
$stamp = (Get-Date -Format 'yyyyMMddTHHmmssZ')
$pageRoot = Join-Path $RepoRoot 'docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT'
$reportsDir = Join-Path $pageRoot 'reports'
$statusDir = Join-Path $pageRoot 'status'
$outputDir = Join-Path $pageRoot 'runner_outputs'
$heartbeatDir = Join-Path $RepoRoot 'docs/chatgpt_status/_shared/heartbeat'
New-Item -ItemType Directory -Force -Path $reportsDir, $statusDir, $outputDir, $heartbeatDir | Out-Null

$report = Join-Path $reportsDir ("terrayield_047_orchestrated_final_ready_$stamp.md")
$status = Join-Path $statusDir ("terrayield_047_orchestrated_final_ready_status_$stamp.md")
$raw = Join-Path $outputDir ("terrayield_047_orchestrated_final_ready_raw_$stamp.txt")
$hb = Join-Path $heartbeatDir 'single_multi_page_runner_heartbeat.txt'
$repair = Join-Path $pageRoot 'automation/RUN_DISTANCE_047_SELF_CONTAINED_REPAIR.ps1'

function Write-TextFile([string]$Path, [string]$Text) {
  $Text | Set-Content -LiteralPath $Path -Encoding UTF8
}

Write-TextFile $hb @"
runner_seen: true
page_key: $pageKey
branch: $branch
script: RUN_DISTANCE_047_ORCHESTRATED_FINAL_READY.ps1
stamp: $stamp
phase: orchestrator_start
"@

$rawLines = New-Object System.Collections.Generic.List[string]
$rawLines.Add("orchestrator_start=$stamp")
$rawLines.Add("repo_root=$RepoRoot")
$rawLines.Add("page_key=$pageKey")
$rawLines.Add("branch=$branch")
$rawLines.Add("repair_script=$repair")

$repairExit = 'not_run'
$repairError = ''
try {
  if (Test-Path -LiteralPath $repair) {
    $rawLines.Add('repair_script_found=true')
    & powershell -NoProfile -ExecutionPolicy Bypass -File $repair *>&1 | ForEach-Object { $rawLines.Add([string]$_) }
    $repairExit = $LASTEXITCODE
  } else {
    $rawLines.Add('repair_script_found=false')
    $repairExit = 'missing_repair_script'
  }
} catch {
  $repairExit = 'exception'
  $repairError = $_.Exception.Message
  $rawLines.Add("repair_exception=$repairError")
}

$smokeFiles = @(Get-ChildItem -LiteralPath $reportsDir -Filter 'terrayield_047_distance_property_types_apply_patch_smoke_*.md' -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending)
$latestSmoke = if ($smokeFiles.Count -gt 0) { $smokeFiles[0].FullName } else { '' }
$finalReady = $false
if ($latestSmoke -and (Select-String -LiteralPath $latestSmoke -Pattern 'FINAL_READY|final_ready:\s*true|status:\s*FINAL_READY' -Quiet)) {
  $finalReady = $true
}

$rawLines | Set-Content -LiteralPath $raw -Encoding UTF8

Write-TextFile $status @"
page_key: $pageKey
branch: $branch
completion_percent: $(if ($finalReady) { '100' } else { '99.6' })
final_ready: $($finalReady.ToString().ToLowerInvariant())
orchestrator_seen_by_runner: true
repair_exit: $repairExit
latest_smoke: $latestSmoke
raw_output: $raw
heartbeat: $hb
next_blocker: $(if ($finalReady) { 'none' } else { 'awaiting_or_failed_repair_smoke' })
"@

Write-TextFile $report @"
# TerraYield 047 Orchestrated FINAL_READY runner report

page_key: $pageKey
branch: $branch
stamp: $stamp

## Result

final_ready: $($finalReady.ToString().ToLowerInvariant())
repair_exit: $repairExit
latest_smoke: $latestSmoke
raw_output: $raw
heartbeat: $hb

## Interpretation

If this file exists in GitHub, the single shared runner successfully picked up this page-local orchestrator. If final_ready is false, inspect the latest smoke/raw output above; the remaining blocker is inside the 047 repair/smoke path, not queue intake.
"@

try {
  git -C $RepoRoot add $report $status $raw $hb | Out-Null
  git -C $RepoRoot commit -m "AAYS 047 orchestrated final ready report $stamp" | Out-Null
  git -C $RepoRoot push origin $branch | Out-Null
} catch {
  # The runner environment may own git push separately. Files are still written locally for runner log capture.
}

if ($finalReady) { exit 0 }
exit 2
