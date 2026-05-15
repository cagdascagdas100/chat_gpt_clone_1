$ErrorActionPreference = 'Continue'
$TaskId = 'aays-103-auto-conservative-completed-labels-20260515'
$BridgeRoot = if ($env:AAYS_BRIDGE_ROOT) { $env:AAYS_BRIDGE_ROOT } else { Split-Path -Parent $PSScriptRoot }
$ResultDir = Join-Path $BridgeRoot 'ai-results'
$HeartbeatDir = Join-Path $BridgeRoot 'ai-heartbeat'
New-Item -ItemType Directory -Force -Path $ResultDir,$HeartbeatDir | Out-Null
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$Report = Join-Path $ResultDir "aays-103-auto-conservative-completed-labels-$Stamp.md"
$OutCsv = Join-Path $ResultDir "aays-103-completed_labels_auto_conservative-$Stamp.csv"
$Heartbeat = Join-Path $HeartbeatDir 'auto-conservative-completed-labels.md'
$Lines = New-Object System.Collections.Generic.List[string]
function L([string]$m){ [void]$Lines.Add($m) }
function Latest([string]$pattern){ Get-ChildItem $ResultDir -Filter $pattern -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1 }
$BaseCsv = Latest 'aays-091-validation-label-template-*.csv'
$SuppCsv = Latest 'aays-092-supplemental-sample-*.csv'
L '# AAYS 103 Auto Conservative Completed Labels'
L ('Generated: ' + (Get-Date -Format s))
L ('TaskId: ' + $TaskId)
L 'Mode: conservative auto-prelabel; no DB writes; no UI patch; not human evidence verification.'
if($null -eq $BaseCsv){ L 'ERROR: base label CSV missing'; Set-Content -Encoding UTF8 -Path $Report -Value $Lines; exit 2 }
if($null -eq $SuppCsv){ L 'ERROR: supplemental sample CSV missing'; Set-Content -Encoding UTF8 -Path $Report -Value $Lines; exit 3 }
$rows = @()
$rows += Import-Csv $BaseCsv.FullName
$rows += Import-Csv $SuppCsv.FullName
$out = foreach($r in $rows){
  $label = 'needs_source'
  $issue = 'missing_source'
  if($r.geometry_verdict -eq 'derived_ai_visual'){ $label = 'needs_source'; $issue = 'geometry_unsupported' }
  elseif($r.geometry_verdict -eq 'derived_signal'){ $label = 'ambiguous'; $issue = 'ambiguous_candidate' }
  elseif($r.geometry_verdict -eq 'derived_multi_signal'){ $label = 'needs_source'; $issue = 'missing_source' }
  $obj = [ordered]@{}
  foreach($p in $r.PSObject.Properties){ $obj[$p.Name] = $p.Value }
  $obj['reviewer_label'] = $label
  $obj['reviewer_confidence'] = 'low'
  $obj['evidence_checked'] = 'no'
  $obj['issue_type'] = $issue
  $obj['corrected_verdict'] = ''
  $obj['reviewer_notes'] = 'AUTO_CONSERVATIVE_PRELABEL: not human verified; do not use to auto-accept; keep production acceptance blocked until evidence is checked.'
  $obj['label_source'] = 'auto_conservative_prelabelling'
  [pscustomobject]$obj
}
$out | Export-Csv -NoTypeInformation -Encoding UTF8 -Path $OutCsv
L ('base_label_csv: ' + $BaseCsv.FullName)
L ('supplemental_sample_csv: ' + $SuppCsv.FullName)
L ('output_completed_labels_auto_csv: ' + $OutCsv)
L ('rows_out: ' + @($out).Count)
L ''
L '## reviewer_label distribution'
$out | Group-Object reviewer_label | Sort-Object Count -Descending | ForEach-Object { L ($_.Name + ': ' + $_.Count) }
L ''
L '## issue_type distribution'
$out | Group-Object issue_type | Sort-Object Count -Descending | ForEach-Object { L ($_.Name + ': ' + $_.Count) }
L ''
L 'manual_review_gate: AUTO_PRELABELS_CREATED_NOT_HUMAN_VERIFIED'
L 'production_acceptance_gate: NOT_READY_FOR_AUTO_ACCEPT'
L 'next_allowed_task: label_outcome_audit_read_only_only'
L 'wide_accuracy_program_percent: 97'
L 'AAYS_103_AUTO_CONSERVATIVE_COMPLETED_LABELS_DONE=true'
Set-Content -Encoding UTF8 -Path $Report -Value $Lines
Set-Content -Encoding UTF8 -Path $Heartbeat -Value $Lines
Write-Output 'AAYS_103_AUTO_CONSERVATIVE_COMPLETED_LABELS_DONE=true'
Write-Output ('REPORT=' + $Report)
Write-Output ('COMPLETED_LABELS_AUTO_CSV=' + $OutCsv)
exit 0
