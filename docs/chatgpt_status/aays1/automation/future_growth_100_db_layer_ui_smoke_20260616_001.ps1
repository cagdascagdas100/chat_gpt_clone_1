# AAYS1 Future Growth 100 completion wrapper
# Existing shared runner only. No new runner is started. No dummy data is generated.
$ErrorActionPreference = 'Continue'
$repoRoot = 'C:\Users\cagda\Documents\GitHub\AAYS'
$statusRoot = Join-Path $repoRoot 'docs\chatgpt_status\aays1'
$reportDir = Join-Path $statusRoot 'reports'
$statusDir = Join-Path $statusRoot 'status'
$heartbeatDir = Join-Path $statusRoot 'heartbeat'
New-Item -ItemType Directory -Force -Path $reportDir,$statusDir,$heartbeatDir | Out-Null
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$report = Join-Path $reportDir ('future_growth_local_admin_smoke_wrapper_' + $stamp + '.txt')
function Add-Line([string]$s) { $s | Add-Content -LiteralPath $report -Encoding UTF8; Write-Host $s }
Add-Line 'page_key=aays1'
Add-Line 'task=future-growth-100-db-layer-ui-smoke'
Add-Line 'runner_mode=existing_shared_runner_only'
Add-Line 'no_new_runner_started=true'
Add-Line 'dummy_data_generated=false'
Add-Line "started_at=$(Get-Date -Format o)"
$handoffRoot = 'F:\AAYS_WORK\future_growth_100_completion_handoff_20260616'
$scriptFile = Get-ChildItem -LiteralPath (Join-Path $handoffRoot 'scripts') -Filter '01_LOCAL_ADMIN_*_POSTGIS_AND_FG_SMOKE.ps1' -File -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $scriptFile) {
  Add-Line 'handoff_script_present=false'
  Add-Line 'completion=82'
  Add-Line 'final_ready=false'
  Add-Line 'product_final_ready=false'
  Add-Line 'production_complete=false'
  Add-Line 'data_gate=HANDOFF_RUNBOOK_MISSING_ON_F_DRIVE'
  "page_key=aays1`ntask=future-growth-100-db-layer-ui-smoke`ncompletion=82`nfinal_ready=false`nproduct_final_ready=false`nproduction_complete=false`ndata_gate=HANDOFF_RUNBOOK_MISSING_ON_F_DRIVE`nreport=$report`nupdated_at=$(Get-Date -Format o)" | Set-Content -LiteralPath (Join-Path $statusDir 'future_growth_100_status_latest.txt') -Encoding UTF8
  "page_key=aays1`nstatus=handoff_runbook_missing`ncompletion=82`nupdated_at=$(Get-Date -Format o)" | Set-Content -LiteralPath (Join-Path $heartbeatDir 'future_growth_100_heartbeat.txt') -Encoding UTF8
  exit 3
}
Add-Line ('handoff_script=' + $scriptFile.FullName)
$childLog = Join-Path $reportDir ('future_growth_local_admin_smoke_child_' + $stamp + '.txt')
try {
  Push-Location $repoRoot
  & $scriptFile.FullName *> $childLog
  $childExit = $LASTEXITCODE
  Pop-Location
} catch {
  try { Pop-Location } catch {}
  $childExit = 9001
  ('wrapper_exception=' + $_.Exception.Message) | Add-Content -LiteralPath $childLog -Encoding UTF8
}
Add-Line ('child_log=' + $childLog)
Add-Line ('child_exit_code=' + $childExit)
$latest = Get-ChildItem -LiteralPath $reportDir -Filter 'future_growth_local_admin_smoke_*.txt' -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if ($latest) { Add-Line ('latest_report=' + $latest.FullName) } else { Add-Line 'latest_report=NONE' }
$ready = $false
if ($latest) {
  $txt = Get-Content -LiteralPath $latest.FullName -Raw -ErrorAction SilentlyContinue
  $ready = (($txt -match 'final_ready=true') -and ($txt -match 'product_final_ready=true') -and ($txt -match 'production_complete=true') -and ($txt -match 'data_gate=NONE'))
}
if ($childExit -eq 0 -and $ready) {
  Add-Line 'completion=100'
  Add-Line 'final_ready=true'
  Add-Line 'product_final_ready=true'
  Add-Line 'production_complete=true'
  Add-Line 'data_gate=NONE'
  "page_key=aays1`ntask=future-growth-100-db-layer-ui-smoke`ncompletion=100`nfinal_ready=true`nproduct_final_ready=true`nproduction_complete=true`ndata_gate=NONE`nreport=$report`nupdated_at=$(Get-Date -Format o)" | Set-Content -LiteralPath (Join-Path $statusDir 'future_growth_100_status_latest.txt') -Encoding UTF8
  "page_key=aays1`nstatus=final_ready`ncompletion=100`nupdated_at=$(Get-Date -Format o)" | Set-Content -LiteralPath (Join-Path $heartbeatDir 'future_growth_100_heartbeat.txt') -Encoding UTF8
  exit 0
}
Add-Line 'completion=84'
Add-Line 'final_ready=false'
Add-Line 'product_final_ready=false'
Add-Line 'production_complete=false'
Add-Line 'data_gate=LOCAL_RUNTIME_SMOKE_NOT_YET_PASSING'
"page_key=aays1`ntask=future-growth-100-db-layer-ui-smoke`ncompletion=84`nfinal_ready=false`nproduct_final_ready=false`nproduction_complete=false`ndata_gate=LOCAL_RUNTIME_SMOKE_NOT_YET_PASSING`nreport=$report`nchild_exit_code=$childExit`nupdated_at=$(Get-Date -Format o)" | Set-Content -LiteralPath (Join-Path $statusDir 'future_growth_100_status_latest.txt') -Encoding UTF8
"page_key=aays1`nstatus=child_run_finished_not_final`ncompletion=84`nupdated_at=$(Get-Date -Format o)" | Set-Content -LiteralPath (Join-Path $heartbeatDir 'future_growth_100_heartbeat.txt') -Encoding UTF8
exit 4
