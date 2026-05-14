$ErrorActionPreference = 'Continue'
$TaskId = 'aays-094-risk-label-spec-20260515'
$BridgeRoot = if ($env:AAYS_BRIDGE_ROOT) { $env:AAYS_BRIDGE_ROOT } else { Split-Path -Parent $PSScriptRoot }
$ResultDir = Join-Path $BridgeRoot 'ai-results'
$HeartbeatDir = Join-Path $BridgeRoot 'ai-heartbeat'
New-Item -ItemType Directory -Force -Path $ResultDir,$HeartbeatDir | Out-Null
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$Report = Join-Path $ResultDir "aays-094-risk-label-spec-$Stamp.md"
$Heartbeat = Join-Path $HeartbeatDir 'risk-label-spec.md'
$Lines = New-Object System.Collections.Generic.List[string]
function L([string]$m){ [void]$Lines.Add($m) }
L '# AAYS 094 Risk Label Spec'
L ('Generated: ' + (Get-Date -Format s))
L ('TaskId: ' + $TaskId)
L 'Mode: read-only implementation spec; no DB writes; no UI patch.'
L ''
L '## New derived fields'
L 'risk_label: low, medium, high, critical'
L 'acceptance_status: accept_candidate, manual_review, needs_source, reject'
L 'policy_reason: semicolon-separated deterministic reasons'
L ''
L '## Deterministic rules v1'
L 'critical: verified_polygon_geojson is null or empty -> acceptance_status=manual_review'
L 'high: geometry_verdict == derived_ai_visual -> acceptance_status=manual_review'
L 'high: normalized_area_m2 < 100 -> acceptance_status=manual_review'
L 'high: normalized_area_m2 > 25000 -> acceptance_status=manual_review'
L 'high: ask_price > 3000000 -> acceptance_status=manual_review'
L 'high: price_per_m2 > 5000 -> acceptance_status=manual_review'
L 'medium: geometry_verdict == derived_signal -> acceptance_status=manual_review'
L 'low: geometry_verdict == derived_multi_signal and source/postcode/authority checks pass -> acceptance_status=accept_candidate'
L ''
L '## Safe implementation sequence'
L '1. Add read-only transformation that computes risk_label and acceptance_status into an output CSV.'
L '2. Do not overwrite source CSV.'
L '3. Compare distribution before/after.'
L '4. Review the 26-row manual validation set before changing thresholds.'
L '5. Only after labels exist, promote to DB schema or UI.'
L ''
L '## Expected next task'
L 'AAYS 095 should generate a risk-labeled preview CSV from stg_land_sales_50step_db_ready.csv without DB writes.'
L ''
L 'wide_accuracy_program_percent: 72'
L 'AAYS_094_RISK_LABEL_SPEC_DONE=true'
Set-Content -Encoding UTF8 -Path $Report -Value $Lines
Set-Content -Encoding UTF8 -Path $Heartbeat -Value $Lines
Write-Output 'AAYS_094_RISK_LABEL_SPEC_DONE=true'
Write-Output ('REPORT=' + $Report)
exit 0
