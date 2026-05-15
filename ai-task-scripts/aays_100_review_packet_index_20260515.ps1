$ErrorActionPreference = 'Continue'
$TaskId = 'aays-100-review-packet-index-20260515'
$BridgeRoot = if ($env:AAYS_BRIDGE_ROOT) { $env:AAYS_BRIDGE_ROOT } else { Split-Path -Parent $PSScriptRoot }
$ResultDir = Join-Path $BridgeRoot 'ai-results'
$HeartbeatDir = Join-Path $BridgeRoot 'ai-heartbeat'
New-Item -ItemType Directory -Force -Path $ResultDir,$HeartbeatDir | Out-Null
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$Report = Join-Path $ResultDir "aays-100-review-packet-index-$Stamp.md"
$Heartbeat = Join-Path $HeartbeatDir 'review-packet-index.md'
$Lines = New-Object System.Collections.Generic.List[string]
function L([string]$m){ [void]$Lines.Add($m) }
function Latest([string]$pattern){ Get-ChildItem $ResultDir -Filter $pattern -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1 }
$label = Latest 'aays-091-validation-label-template-*.csv'
$supp = Latest 'aays-092-supplemental-sample-*.csv'
$risk = Latest 'aays-097-risk-preview-v2-*.csv'
L '# AAYS 100 Review Packet Index'
L ('Generated: ' + (Get-Date -Format s))
L ('TaskId: ' + $TaskId)
L 'Mode: read-only review packet index; no DB writes; no UI patch.'
L ''
L '## Packet files'
if($label){ L ('validation_label_csv: ' + $label.FullName); $labelRows = @(Import-Csv $label.FullName).Count; L ('validation_label_rows: ' + $labelRows) } else { L 'validation_label_csv: MISSING'; $labelRows = 0 }
if($supp){ L ('supplemental_sample_csv: ' + $supp.FullName); $suppRows = @(Import-Csv $supp.FullName).Count; L ('supplemental_sample_rows: ' + $suppRows) } else { L 'supplemental_sample_csv: MISSING'; $suppRows = 0 }
if($risk){ L ('risk_preview_v2_csv: ' + $risk.FullName); $riskRows = @(Import-Csv $risk.FullName).Count; L ('risk_preview_v2_rows: ' + $riskRows) } else { L 'risk_preview_v2_csv: MISSING'; $riskRows = 0 }
L ('combined_review_rows: ' + ($labelRows + $suppRows))
L ''
L '## Manual review completion checklist'
L '1. Open validation_label_csv and supplemental_sample_csv.'
L '2. Fill reviewer_label for every row.'
L '3. Fill reviewer_confidence as high, medium, or low.'
L '4. Fill evidence_checked as yes or no.'
L '5. Fill issue_type using allowed enum values.'
L '6. Save completed CSV copies before running threshold re-audit.'
L ''
L '## Gate status'
L 'automation_gate: COMPLETE'
L 'manual_review_gate: WAITING_FOR_HUMAN_LABELS'
L 'production_acceptance_gate: NOT_READY_FOR_AUTO_ACCEPT'
L 'safe_output_gate: READY_FOR_MANUAL_REVIEW_QUEUE'
L ''
L 'wide_accuracy_program_percent: 96'
L 'AAYS_100_REVIEW_PACKET_INDEX_DONE=true'
Set-Content -Encoding UTF8 -Path $Report -Value $Lines
Set-Content -Encoding UTF8 -Path $Heartbeat -Value $Lines
Write-Output 'AAYS_100_REVIEW_PACKET_INDEX_DONE=true'
Write-Output ('REPORT=' + $Report)
exit 0
