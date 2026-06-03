$ErrorActionPreference = 'Continue'
$TaskId = 'aays-099-final-handoff-20260515'
$BridgeRoot = if ($env:AAYS_BRIDGE_ROOT) { $env:AAYS_BRIDGE_ROOT } else { Split-Path -Parent $PSScriptRoot }
$ResultDir = Join-Path $BridgeRoot 'ai-results'
$HeartbeatDir = Join-Path $BridgeRoot 'ai-heartbeat'
New-Item -ItemType Directory -Force -Path $ResultDir,$HeartbeatDir | Out-Null
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$Report = Join-Path $ResultDir "aays-099-final-handoff-$Stamp.md"
$Heartbeat = Join-Path $HeartbeatDir 'final-handoff.md'
$Lines = New-Object System.Collections.Generic.List[string]
function AddLine([string]$m){ [void]$Lines.Add($m) }
function AddPathStatus([string]$label,[string]$path){ if(Test-Path $path){ AddLine ("OK: $label = $path") } else { AddLine ("MISSING: $label = $path") } }
AddLine '# AAYS 099 Final Handoff Summary'
AddLine ('Generated: ' + (Get-Date -Format s))
AddLine ('TaskId: ' + $TaskId)
AddLine 'Mode: read-only final handoff; no DB writes; no UI patch.'
AddLine ''
AddLine '## Completed milestones'
AddLine 'db_dryrun: complete'
AddLine 'schema_apply: complete'
AddLine 'csv_import: complete, 120 rows'
AddLine 'source_inventory: complete'
AddLine 'validation_sample: complete, 26 review rows'
AddLine 'anomaly_threshold_audit: complete'
AddLine 'threshold_policy_pack: complete'
AddLine 'risk_preview_v2: complete'
AddLine 'production_readiness_gate: complete'
AddLine ''
AddLine '## Key output paths'
AddPathStatus 'source csv' 'E:\AAYS_DATA\land_sales\final_outputs\stg_land_sales_50step_db_ready.csv'
AddPathStatus 'db schema sql' 'E:\AAYS_DATA\land_sales\final_outputs\DB_SCHEMA_APPLY.sql'
AddPathStatus 'validation label csv' (Join-Path $ResultDir 'aays-091-validation-label-template-20260515_021151.csv')
AddPathStatus 'supplemental sample csv' (Join-Path $ResultDir 'aays-092-supplemental-sample-20260515_022949.csv')
AddPathStatus 'risk preview v2 csv' (Join-Path $ResultDir 'aays-097-risk-preview-v2-20260515_025249.csv')
AddPathStatus 'production readiness heartbeat' (Join-Path $HeartbeatDir 'production-readiness-gate.md')
AddLine ''
AddLine '## Gate decisions'
AddLine 'production_acceptance_gate: NOT_READY_FOR_AUTO_ACCEPT'
AddLine 'safe_output_gate: READY_FOR_MANUAL_REVIEW_QUEUE'
AddLine ''
AddLine '## Current distributions'
AddLine 'source_rows: 120'
AddLine 'risk_label_v2: critical=99, high=21'
AddLine 'acceptance_status_strict: manual_review=120'
AddLine 'review_set_rows: 26'
AddLine ''
AddLine '## Hard blockers'
AddLine '1. verified_polygon_geojson must be present and georeferenced before auto-accept.'
AddLine '2. source_urls_json and listing evidence must be checked for reviewed rows.'
AddLine '3. reviewer labels must be filled for at least 25 rows.'
AddLine '4. threshold changes must wait until label outcomes exist.'
AddLine ''
AddLine '## Recommended next manual steps'
AddLine '1. Open the 26-row validation label CSV and supplemental CSV.'
AddLine '2. Fill reviewer_label, reviewer_confidence, evidence_checked, and issue_type.'
AddLine '3. Re-run threshold audit after labels exist.'
AddLine '4. Only then patch production scoring or UI.'
AddLine ''
AddLine 'wide_accuracy_program_percent: 95'
AddLine 'AAYS_099_FINAL_HANDOFF_DONE=true'
Set-Content -Encoding UTF8 -Path $Report -Value $Lines
Set-Content -Encoding UTF8 -Path $Heartbeat -Value $Lines
Write-Output 'AAYS_099_FINAL_HANDOFF_DONE=true'
Write-Output ('REPORT=' + $Report)
exit 0
