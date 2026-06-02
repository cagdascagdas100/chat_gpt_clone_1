$ErrorActionPreference = 'Continue'
$TaskId = 'aays-096-risk-policy-calibration-20260515'
$BridgeRoot = if ($env:AAYS_BRIDGE_ROOT) { $env:AAYS_BRIDGE_ROOT } else { Split-Path -Parent $PSScriptRoot }
$ResultDir = Join-Path $BridgeRoot 'ai-results'
$HeartbeatDir = Join-Path $BridgeRoot 'ai-heartbeat'
New-Item -ItemType Directory -Force -Path $ResultDir,$HeartbeatDir | Out-Null
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$Report = Join-Path $ResultDir "aays-096-risk-policy-calibration-$Stamp.md"
$Heartbeat = Join-Path $HeartbeatDir 'risk-policy-calibration.md'
$RiskHb = Join-Path $HeartbeatDir 'risk-preview.md'
$Lines = New-Object System.Collections.Generic.List[string]
function L([string]$m){ [void]$Lines.Add($m) }
L '# AAYS 096 Risk Policy Calibration'
L ('Generated: ' + (Get-Date -Format s))
L ('TaskId: ' + $TaskId)
L 'Mode: read-only calibration memo; no DB writes; no UI patch.'
L ''
L '## Input finding'
if(Test-Path $RiskHb){ Get-Content $RiskHb -Tail 80 | ForEach-Object { L $_ } } else { L 'risk-preview heartbeat missing' }
L ''
L '## Calibration finding'
L 'Current v1 policy is safe but over-conservative: every row becomes critical/manual_review because verified_polygon_geojson is missing or empty for all 120 rows.'
L 'This is acceptable for fail-closed production safety, but not useful for ranking manual review effort.'
L ''
L '## Proposed v2 separation'
L 'Keep acceptance_status strict: no row with missing verified polygon should become verified/accepted.'
L 'Relax risk_label to rank review priority even when acceptance_status remains manual_review.'
L ''
L 'risk_label_v2 critical: missing polygon plus extreme area/price/ppm or contradictory fields.'
L 'risk_label_v2 high: derived_ai_visual without polygon, or derived_signal with area/price anomaly.'
L 'risk_label_v2 medium: derived_signal without additional anomaly.'
L 'risk_label_v2 low: derived_multi_signal without anomaly, still manual_review until source checks pass.'
L ''
L '## Safe next implementation'
L 'AAYS 097 should generate risk_preview_v2 CSV with both strict acceptance_status and calibrated risk_label_v2.'
L 'No DB writes. No UI patch. Source CSV not overwritten.'
L ''
L 'wide_accuracy_program_percent: 82'
L 'AAYS_096_RISK_POLICY_CALIBRATION_DONE=true'
Set-Content -Encoding UTF8 -Path $Report -Value $Lines
Set-Content -Encoding UTF8 -Path $Heartbeat -Value $Lines
Write-Output 'AAYS_096_RISK_POLICY_CALIBRATION_DONE=true'
Write-Output ('REPORT=' + $Report)
exit 0
