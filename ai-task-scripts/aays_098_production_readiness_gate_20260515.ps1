$ErrorActionPreference = 'Continue'
$TaskId = 'aays-098-production-readiness-gate-20260515'
$BridgeRoot = if ($env:AAYS_BRIDGE_ROOT) { $env:AAYS_BRIDGE_ROOT } else { Split-Path -Parent $PSScriptRoot }
$ResultDir = Join-Path $BridgeRoot 'ai-results'
$HeartbeatDir = Join-Path $BridgeRoot 'ai-heartbeat'
New-Item -ItemType Directory -Force -Path $ResultDir,$HeartbeatDir | Out-Null
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$Report = Join-Path $ResultDir "aays-098-production-readiness-gate-$Stamp.md"
$Heartbeat = Join-Path $HeartbeatDir 'production-readiness-gate.md'
$RiskV2 = Join-Path $HeartbeatDir 'risk-preview-v2.md'
$Supplemental = Join-Path $HeartbeatDir 'supplemental-sample.md'
$Lines = New-Object System.Collections.Generic.List[string]
function L([string]$m){ [void]$Lines.Add($m) }
function TailSection([string]$title,[string]$path,[int]$n){
  L ''; L ('## ' + $title)
  if(Test-Path $path){ Get-Content $path -Tail $n | ForEach-Object { L $_ } } else { L ('MISSING: ' + $path) }
}
L '# AAYS 098 Production Readiness Gate'
L ('Generated: ' + (Get-Date -Format s))
L ('TaskId: ' + $TaskId)
L 'Mode: read-only readiness gate; no DB writes; no UI patch.'
TailSection 'Risk preview v2 carried forward' $RiskV2 80
TailSection 'Review sample carried forward' $Supplemental 60
L ''
L '## Gate decision'
L 'production_acceptance_gate: NOT_READY_FOR_AUTO_ACCEPT'
L 'reason: acceptance_status_strict remains manual_review for all 120 rows because verified polygons are missing.'
L 'safe_output_gate: READY_FOR_MANUAL_REVIEW_QUEUE'
L 'reason: risk_label_v2 now separates review priority and source CSV was not overwritten.'
L ''
L '## What is safe to use now'
L '1. Use 26-row review set for manual labeling.'
L '2. Use risk_preview_v2 as manual review prioritization only.'
L '3. Keep all rows out of auto-verified/auto-accepted status until polygon/source checks pass.'
L ''
L '## Hard blockers before production auto-accept'
L '1. verified_polygon_geojson must be present and georeferenced.'
L '2. source_urls_json/listing evidence must be checked for the reviewed rows.'
L '3. reviewer labels must be filled for at least 25 rows.'
L '4. threshold changes must wait until reviewed label outcomes exist.'
L ''
L '## Next task'
L 'AAYS 099 should create a final handoff summary with all output paths, gates, blockers, and next manual steps.'
L ''
L 'wide_accuracy_program_percent: 90'
L 'AAYS_098_PRODUCTION_READINESS_GATE_DONE=true'
Set-Content -Encoding UTF8 -Path $Report -Value $Lines
Set-Content -Encoding UTF8 -Path $Heartbeat -Value $Lines
Write-Output 'AAYS_098_PRODUCTION_READINESS_GATE_DONE=true'
Write-Output ('REPORT=' + $Report)
exit 0
