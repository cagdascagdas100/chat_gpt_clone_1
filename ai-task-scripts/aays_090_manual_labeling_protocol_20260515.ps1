$ErrorActionPreference = 'Continue'
$TaskId = 'aays-090-manual-labeling-protocol-20260515'
$BridgeRoot = if ($env:AAYS_BRIDGE_ROOT) { $env:AAYS_BRIDGE_ROOT } else { Split-Path -Parent $PSScriptRoot }
$ResultDir = Join-Path $BridgeRoot 'ai-results'
$HeartbeatDir = Join-Path $BridgeRoot 'ai-heartbeat'
New-Item -ItemType Directory -Force -Path $ResultDir,$HeartbeatDir | Out-Null
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$Report = Join-Path $ResultDir "aays-090-manual-labeling-protocol-$Stamp.md"
$Heartbeat = Join-Path $HeartbeatDir 'manual-labeling-protocol.md'
$Lines = New-Object System.Collections.Generic.List[string]
function L([string]$m){ [void]$Lines.Add($m) }
L '# AAYS 090 Manual Labeling Protocol'
L ('Generated: ' + (Get-Date -Format s))
L ('TaskId: ' + $TaskId)
L 'Mode: read-only protocol; no DB writes; no UI patch.'
L ''
L '## Inputs already produced'
L 'gate_1_source_inventory: done'
L 'gate_2_schema_map: partial_from_headers_and_schema'
L 'gate_3_validation_sample: done'
L 'gate_4_anomaly_threshold_audit: done_or_local_report_available'
L ''
L '## Manual validation labels'
L 'accept: evidence supports geometry_verdict and key fields.'
L 'downgrade: evidence exists but confidence/verdict should be lower.'
L 'reject: evidence contradicts geometry_verdict or key fields.'
L 'needs_source: insufficient source_urls_json/listing evidence.'
L 'ambiguous: multiple plausible parcel/geometry candidates.'
L ''
L '## Required fields per reviewed row'
L 'validation_case_id, verification_id, listing_id, reviewer_label, reviewer_confidence, evidence_checked, issue_type, corrected_verdict, notes'
L ''
L '## Review rules'
L '1. Review at least 25 rows before changing thresholds.'
L '2. Include all derived_multi_signal rows in the first pass.'
L '3. Include derived_signal rows with high uncertainty or missing source evidence.'
L '4. Include representative derived_ai_visual rows because they dominate distribution.'
L '5. Do not auto-promote any row with missing canonical URL or source_urls_json.'
L ''
L '## Threshold adjustment proposal after labels'
L 'If accept rate >= 90 percent for derived_multi_signal, preserve or raise confidence.'
L 'If accept rate < 75 percent for derived_signal, downgrade scoring weight.'
L 'If accept rate < 70 percent for derived_ai_visual, require extra source evidence before verified status.'
L 'If needs_source > 15 percent, source inventory must block production scoring.'
L ''
L '## Next task'
L 'AAYS 091 should produce a validation label CSV template and, if sample CSV exists, join it into a review-ready workbook/CSV.'
L ''
L 'wide_accuracy_program_percent: 55'
L 'AAYS_090_MANUAL_LABELING_PROTOCOL_DONE=true'
Set-Content -Encoding UTF8 -Path $Report -Value $Lines
Set-Content -Encoding UTF8 -Path $Heartbeat -Value $Lines
Write-Output 'AAYS_090_MANUAL_LABELING_PROTOCOL_DONE=true'
Write-Output ('REPORT=' + $Report)
exit 0
