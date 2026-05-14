$ErrorActionPreference = 'Continue'
$TaskId = 'aays-092-implementation-readiness-pack-20260515'
$BridgeRoot = if ($env:AAYS_BRIDGE_ROOT) { $env:AAYS_BRIDGE_ROOT } else { Split-Path -Parent $PSScriptRoot }
$ResultDir = Join-Path $BridgeRoot 'ai-results'
$HeartbeatDir = Join-Path $BridgeRoot 'ai-heartbeat'
New-Item -ItemType Directory -Force -Path $ResultDir,$HeartbeatDir | Out-Null
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$Report = Join-Path $ResultDir "aays-092-implementation-readiness-pack-$Stamp.md"
$Heartbeat = Join-Path $HeartbeatDir 'implementation-readiness-pack.md'
$Policy = Join-Path $HeartbeatDir 'threshold-policy-pack.md'
$Labels = Join-Path $HeartbeatDir 'validation-label-template.md'
$Anomaly = Join-Path $HeartbeatDir 'anomaly-threshold-audit.md'
$Lines = New-Object System.Collections.Generic.List[string]
function AddLine([string]$m){ [void]$Lines.Add($m) }
function AddFileExcerpt([string]$title,[string]$path,[int]$top){
  AddLine ''; AddLine ('## ' + $title)
  if(Test-Path $path){ Get-Content $path -TotalCount $top | ForEach-Object { AddLine $_ } } else { AddLine ('MISSING_FILE: ' + $path) }
}
AddLine '# AAYS 092 Implementation Readiness Pack'
AddLine ('Generated: ' + (Get-Date -Format s))
AddLine ('TaskId: ' + $TaskId)
AddLine 'Mode: read-only implementation readiness; no DB writes; no UI patch.'
AddFileExcerpt 'Policy pack excerpt' $Policy 80
AddFileExcerpt 'Validation template excerpt' $Labels 80
AddFileExcerpt 'Anomaly audit excerpt' $Anomaly 80
AddLine ''
AddLine '## Implementation spec v1'
AddLine 'field_risk_label_values: low, medium, high, critical'
AddLine 'field_acceptance_status_values: accept_candidate, manual_review, needs_source, reject'
AddLine 'risk_rule_critical_no_polygon: verified_polygon_geojson null/empty -> critical + manual_review or needs_source'
AddLine 'risk_rule_high_ai_visual: derived_ai_visual -> high + manual_review'
AddLine 'risk_rule_high_price: ask_price > 3000000 -> high + manual_review'
AddLine 'risk_rule_high_area: normalized_area_m2 > 25000 -> high + manual_review'
AddLine 'risk_rule_high_ppm: price_per_m2 > 5000 -> high + manual_review'
AddLine 'risk_rule_low_area: normalized_area_m2 < 100 -> high + manual_review'
AddLine 'risk_rule_medium_signal: derived_signal -> medium + manual_review until validation labels exist'
AddLine 'risk_rule_medium_multi_signal: derived_multi_signal -> medium + accept_candidate only if source evidence is checked'
AddLine ''
AddLine '## Test plan v1'
AddLine 'test_1: no missing core fields should pass completeness audit.'
AddLine 'test_2: all derived_ai_visual rows produce high/manual_review.'
AddLine 'test_3: no polygon rows cannot be marked verified.'
AddLine 'test_4: high area/price/ppm rows are surfaced in review queue.'
AddLine 'test_5: validation label CSV accepted values only.'
AddLine ''
AddLine '## Next gates'
AddLine 'gate_6_implementation_spec: done'
AddLine 'gate_7_code_patch_or_config_patch: next'
AddLine 'gate_8_unit_tests: next_after_patch'
AddLine 'wide_accuracy_program_percent: 65'
AddLine 'AAYS_092_IMPLEMENTATION_READINESS_PACK_DONE=true'
Set-Content -Encoding UTF8 -Path $Report -Value $Lines
Set-Content -Encoding UTF8 -Path $Heartbeat -Value $Lines
Write-Output 'AAYS_092_IMPLEMENTATION_READINESS_PACK_DONE=true'
Write-Output ('REPORT=' + $Report)
exit 0
