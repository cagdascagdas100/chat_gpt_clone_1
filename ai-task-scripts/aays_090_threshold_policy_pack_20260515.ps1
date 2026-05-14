$ErrorActionPreference = 'Continue'
$TaskId = 'aays-090-threshold-policy-pack-20260515'
$BridgeRoot = if ($env:AAYS_BRIDGE_ROOT) { $env:AAYS_BRIDGE_ROOT } else { Split-Path -Parent $PSScriptRoot }
$ResultDir = Join-Path $BridgeRoot 'ai-results'
$HeartbeatDir = Join-Path $BridgeRoot 'ai-heartbeat'
New-Item -ItemType Directory -Force -Path $ResultDir,$HeartbeatDir | Out-Null
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$Report = Join-Path $ResultDir "aays-090-threshold-policy-pack-$Stamp.md"
$Heartbeat = Join-Path $HeartbeatDir 'threshold-policy-pack.md'
$Validation = Join-Path $HeartbeatDir 'validation-sample.md'
$Anomaly = Join-Path $HeartbeatDir 'anomaly-threshold-audit.md'
$Lines = New-Object System.Collections.Generic.List[string]
function AddLine([string]$m){ [void]$Lines.Add($m) }
function AddSection($title,$path,$pattern){
  AddLine ''; AddLine ('## ' + $title)
  if(Test-Path $path){
    $hits = Select-String -Path $path -Pattern $pattern -SimpleMatch -ErrorAction SilentlyContinue
    if($hits){ $hits | ForEach-Object { AddLine $_.Line } } else { AddLine 'NO_HITS' }
  } else { AddLine ('MISSING_FILE: ' + $path) }
}
AddLine '# AAYS 090 Threshold Policy Pack'
AddLine ('Generated: ' + (Get-Date -Format s))
AddLine ('TaskId: ' + $TaskId)
AddLine 'Mode: read-only policy pack; no DB writes; no UI patch.'
AddSection 'Verdict distribution carried forward' $Validation 'derived_'
AddSection 'Completeness counts carried forward' $Anomaly 'missing_'
AddSection 'Suggested threshold rules carried forward' $Anomaly 'rule_'
AddLine ''
AddLine '## Proposed review policy v1'
AddLine 'policy_accept_candidate: derived_multi_signal rows may be promoted only after external source URL and postcode authority check.'
AddLine 'policy_manual_review_required: all derived_ai_visual rows remain manual_review unless georeferenced polygon evidence is present.'
AddLine 'policy_area_low_review: normalized_area_m2 < 100 requires manual review.'
AddLine 'policy_area_high_review: normalized_area_m2 > 25000 requires manual review.'
AddLine 'policy_price_high_review: ask_price > 3000000 requires manual review.'
AddLine 'policy_ppm_high_review: price_per_m2 > 5000 requires manual review.'
AddLine 'policy_missing_core_fields: missing postcode, authority, price, or area is reject_or_needs_source.'
AddLine 'policy_no_polygon: verified_polygon_geojson null/empty cannot be marked verified.'
AddLine ''
AddLine '## Implementation backlog'
AddLine '1. Add deterministic risk_label field in downstream scoring.'
AddLine '2. Add acceptance_status enum: accept_candidate, manual_review, needs_source, reject.'
AddLine '3. Build 25-row manual validation truth table from AAYS 088 sample.'
AddLine '4. Re-run threshold audit after truth table labels are added.'
AddLine '5. Only then adjust scoring thresholds.'
AddLine ''
AddLine 'wide_accuracy_program_percent: 55'
AddLine 'AAYS_090_THRESHOLD_POLICY_PACK_DONE=true'
Set-Content -Encoding UTF8 -Path $Report -Value $Lines
Set-Content -Encoding UTF8 -Path $Heartbeat -Value $Lines
Write-Output 'AAYS_090_THRESHOLD_POLICY_PACK_DONE=true'
Write-Output ('REPORT=' + $Report)
exit 0
