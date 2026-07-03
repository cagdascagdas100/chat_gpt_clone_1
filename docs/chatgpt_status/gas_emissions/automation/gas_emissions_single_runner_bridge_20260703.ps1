param(
  [string]$VerifiedRowsCsv = "docs/chatgpt_status/gas_emissions/fixtures/gas_emissions_verified_rows_template_20260703.csv",
  [string]$SiteVisibleJson = "outputs/england_program_parcel_matrix_20260629/gas_emissions_updates/latest_changes.json"
)
$ErrorActionPreference = "Stop"
function NowUtc { (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ") }
function Safe-NewDir([string]$p) { if (-not (Test-Path -LiteralPath $p)) { New-Item -ItemType Directory -Force -Path $p | Out-Null } }
$RepoRoot = if ($env:AAYS_REPO_ROOT) { $env:AAYS_REPO_ROOT } else { (Resolve-Path ".").Path }
$RowsPath = Join-Path $RepoRoot $VerifiedRowsCsv
$JsonPath = Join-Path $RepoRoot $SiteVisibleJson
$Base = Join-Path $RepoRoot "docs/chatgpt_status/gas_emissions"
$ReportDir = Join-Path $Base "reports"
$StatusDir = Join-Path $Base "status"
$HeartbeatDir = Join-Path $Base "heartbeat"
Safe-NewDir $ReportDir; Safe-NewDir $StatusDir; Safe-NewDir $HeartbeatDir; Safe-NewDir (Split-Path -Parent $JsonPath)
$blockers = @()
function Add-Blocker([string]$code,[string]$detail){ $script:blockers += [ordered]@{code=$code;severity="blocking";detail=$detail} }
$rows = @()
if (Test-Path -LiteralPath $RowsPath) { $rows = @(Import-Csv -LiteralPath $RowsPath) } else { Add-Blocker "missing_verified_rows_csv" "Verified rows CSV is missing." }
$realRows = @($rows | Where-Object { $_.parcel_id -and $_.parcel_id -notlike "REPLACE_WITH_*" -and $_.emission_percent -match "^[0-9]+(\.[0-9]+)?$" -and $_.source_url -and $_.source_url -notlike "REPLACE_WITH_*" -and $_.source_date -match "^\d{4}-\d{2}-\d{2}$" -and $_.matching_method -and $_.calculation_explanation })
if ($realRows.Count -eq 0) { Add-Blocker "missing_verified_source_backed_rows" "No real source-backed Gas Emissions parcel rows were found in the fixture CSV." }
$appCandidates = @("england_map_web/app.js","app.js") | ForEach-Object { Join-Path $RepoRoot $_ }
$appPath = $appCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
$uiGate = $false
if ($appPath) {
  $app = Get-Content -LiteralPath $appPath -Raw
  $runtimePatchText = ''
  try {
    $runtimePatchFiles = @(Get-ChildItem -LiteralPath $RepoRoot -Recurse -File -Filter 'gas_emissions_runtime_patch_20260703.js' -ErrorAction SilentlyContinue)
    foreach ($pf in $runtimePatchFiles) { $runtimePatchText += "`n" + (Get-Content -LiteralPath $pf.FullName -Raw) }
  } catch {}
  $uiText = $app + "`n" + $runtimePatchText
  $tokens = @("Gas Emissions","emission_percent","risk_color","confidence","source_date","matching_method","calculation_explanation","air.png")
  $missing = @($tokens | Where-Object { $uiText -notmatch [regex]::Escape($_) })
  if ($missing.Count -eq 0) { $uiGate = $true } else { Add-Blocker "missing_ui_tokens" ("app.js missing tokens: " + ($missing -join ", ")) }
} else { Add-Blocker "missing_app_js" "No app.js found at expected paths." }
$smokePath = Join-Path $ReportDir "gas_emissions_browser_smoke_20260703.json"
$browserGate = $false
if (Test-Path -LiteralPath $smokePath) {
  try { $smoke = Get-Content -LiteralPath $smokePath -Raw | ConvertFrom-Json; $browserGate = [bool]$smoke.passed; if (-not $browserGate) { Add-Blocker "browser_smoke_failed" "Browser smoke exists but did not pass." } } catch { Add-Blocker "browser_smoke_invalid_json" $_.Exception.Message }
} else { Add-Blocker "missing_browser_smoke_result" "Browser smoke result for local 8020 matrix site is missing." }
$changes = @($realRows | ForEach-Object {
  $needReview = $true; try { $needReview = [System.Convert]::ToBoolean($_.needs_manual_review) } catch {}
  $changed = $false; try { $changed = [System.Convert]::ToBoolean($_.changed_in_latest_run) } catch {}
  [ordered]@{ parcel_id=$_.parcel_id; parcel_ref=$_.parcel_ref; emission_percent=[double]$_.emission_percent; level=$_.gas_emission_level; gas_emission_level=$_.gas_emission_level; risk_color=$_.risk_color; confidence=[double]$_.confidence_percent; confidence_percent=[double]$_.confidence_percent; source=$_.source; source_url=$_.source_url; source_date=$_.source_date; matching_method=$_.matching_method; calculation_explanation=$_.calculation_explanation; accuracy_score_4=[double]$_.accuracy_score_4; needs_manual_review=$needReview; changed_in_latest_run=$changed }
})
$sourceGate = ($changes.Count -gt 0) -and (@($changes | Where-Object { $_.accuracy_score_4 -lt 3 -or $_.needs_manual_review }).Count -eq 0)
$finalReady = $sourceGate -and $uiGate -and $browserGate -and ($blockers.Count -eq 0)
$score = if($finalReady){"4/4"}elseif($sourceGate -and $uiGate){"3/4"}elseif($changes.Count -gt 0){"2/4"}elseif($uiGate){"1/4"}else{"0/4"}
$payload = [ordered]@{ layer="Gas Emissions"; program_output="Gas Emission Level"; status=if($finalReady){"FINAL_READY_SITE_VISIBLE_BROWSER_SMOKE_PASS"}else{"BLOCKED_SINGLE_RUNNER_EVIDENCE_INCOMPLETE"}; fake_data=$false; db_write=$false; migration_apply=$false; prod_deploy=$false; last_updated=(NowUtc); runner_status="single_runner_bridge_completed"; source_row_gate_passed=$sourceGate; ui_token_gate_passed=$uiGate; browser_smoke_passed=$browserGate; verification_score_after=$score; final_ready=$finalReady; manual_review_required=(-not $finalReady); changes=$changes; blockers=@($blockers); next_action=if($finalReady){"Gas Emissions can be marked complete."}else{"Resolve blockers and rerun the same single bridge."} }
$payload | ConvertTo-Json -Depth 40 | Set-Content -LiteralPath $JsonPath -Encoding UTF8
Set-Content -LiteralPath (Join-Path $StatusDir "gas_emissions_current_status_20260703.txt") -Value @("layer=Gas Emissions","program_output=Gas Emission Level","final_ready=$finalReady","verification_score_after=$score","blocker_count=$($blockers.Count)","updated_at=$(NowUtc)") -Encoding UTF8
Set-Content -LiteralPath (Join-Path $HeartbeatDir "gas_emissions_single_runner_bridge_20260703_heartbeat.txt") -Value "heartbeat=$(NowUtc)" -Encoding UTF8
Set-Content -LiteralPath (Join-Path $ReportDir "gas_emissions_progress_latest_20260703.md") -Value @("# Gas Emissions Progress Latest","","updated_at=$(NowUtc)","final_ready=$finalReady","verification_score_after=$score","blocker_count=$($blockers.Count)","source_row_gate_passed=$sourceGate","ui_token_gate_passed=$uiGate","browser_smoke_passed=$browserGate","","## Blockers",($blockers | ConvertTo-Json -Depth 20),"","## Next Action",$payload.next_action) -Encoding UTF8
Write-Output "gas_emissions_single_runner_bridge_completed final_ready=$finalReady score=$score blockers=$($blockers.Count)"
