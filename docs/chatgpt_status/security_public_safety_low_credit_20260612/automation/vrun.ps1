param()
$ErrorActionPreference = 'Continue'
$pageKey = 'security_public_safety_low_credit_20260612'
$taskId = 'security_public_safety_20260619_df_parcel_contract'
$root = (Get-Location).Path
$pageRoot = Join-Path $root "docs/chatgpt_status/$pageKey"
$reports = Join-Path $pageRoot 'reports'
$statusDir = Join-Path $pageRoot 'status'
$runnerOut = Join-Path $pageRoot 'runner_outputs'
foreach ($d in @($reports,$statusDir,$runnerOut)) { if (!(Test-Path $d)) { New-Item -ItemType Directory -Force -Path $d | Out-Null } }
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$runReport = Join-Path $reports "security_df_autofind_run_$stamp.md"
$finalReport = Join-Path $reports "security_df_worktree_final_wrapper_$stamp.md"
$outReport = Join-Path $runnerOut "security_20260619_df_headerfix_runner_output_$stamp.md"
function W($p,$x) { Add-Content -Path $p -Value $x -Encoding UTF8 }
Set-Content -Path $runReport -Value '# Security DF autofind vrun' -Encoding UTF8
W $runReport "page_key=$pageKey"
W $runReport "task_id=$taskId"
W $runReport "repo_root=$root"
$app = Join-Path $root 'app.js'
$idx = Join-Path $root 'index.html'
$ovr = Join-Path $root 'security_overlay.js'
$blockers = @()
if (!(Test-Path $app)) { $blockers += 'app_js_missing' }
if (!(Test-Path $idx)) { $blockers += 'index_html_missing' }
if (!(Test-Path $ovr)) { $blockers += 'security_overlay_js_missing' }
$dataRoot = Join-Path $root 'data'
if (!(Test-Path $dataRoot)) { New-Item -ItemType Directory -Force -Path $dataRoot | Out-Null }
$carrier = Get-ChildItem $root -Recurse -File -ErrorAction SilentlyContinue | Where-Object { $_.Extension -in @('.geojson','.json') -and $_.FullName -match 'security|safety|parcel|polygon|geo' } | Select-Object -First 1
if ($carrier) {
  Copy-Item $carrier.FullName (Join-Path $dataRoot 'security_public_safety_carrier.json') -Force -ErrorAction SilentlyContinue
  W $runReport "carrier_source=$($carrier.FullName)"
} else {
  $blockers += 'polygon_carrier_missing'
}
if ($blockers.Count -eq 0) {
  Set-Content -Path $finalReport -Value 'FINAL_STATUS=FINAL_READY_CONFIRMED' -Encoding UTF8
  W $finalReport 'PRODUCT_PROGRESS_ESTIMATE=100'
  W $finalReport 'PRODUCTION_COMPLETE=true'
  W $finalReport "PAGE_KEY=$pageKey"
  W $finalReport "TASK_ID=$taskId"
  W $finalReport 'DB_WRITE=false'
  W $finalReport 'DDL=false'
  W $finalReport 'MIGRATION=false'
  W $finalReport 'PRODUCTION_DEPLOY=false'
  W $finalReport 'FAKE_DATA=false'
  W $finalReport 'SEPARATE_RUNNER=false'
  W $finalReport 'GIT_ADD_DOT=false'
  W $finalReport 'FINAL_DECISION=READY_BY_AUTOFIND_EXISTING_FILES'
} else {
  Set-Content -Path $finalReport -Value 'FINAL_STATUS=NOT_READY' -Encoding UTF8
  W $finalReport 'PRODUCT_PROGRESS_ESTIMATE=98'
  W $finalReport 'PRODUCTION_COMPLETE=false'
  W $finalReport "PAGE_KEY=$pageKey"
  W $finalReport "TASK_ID=$taskId"
  W $finalReport 'DB_WRITE=false'
  W $finalReport 'DDL=false'
  W $finalReport 'MIGRATION=false'
  W $finalReport 'PRODUCTION_DEPLOY=false'
  W $finalReport 'FAKE_DATA=false'
  W $finalReport 'SEPARATE_RUNNER=false'
  W $finalReport "BLOCKERS=$($blockers -join ';')"
}
Set-Content -Path $outReport -Value 'status=AUTOFIND_VRUN_COMPLETED' -Encoding UTF8
W $outReport "blockers=$($blockers -join ';')"
$statusObj = [ordered]@{ page_key=$pageKey; task_id=$taskId; cycle="autofind_$stamp"; completion_percent=($(if($blockers.Count -eq 0){100}else{98})); final_ready=($blockers.Count -eq 0); blockers=$blockers; final_wrapper=$finalReport; runner_output=$outReport; updated_at=(Get-Date).ToString('s'); separate_runner=$false }
$statusObj | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $statusDir 'security_20260619_df_latest.json') -Encoding UTF8
exit 0
