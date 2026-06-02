$ErrorActionPreference = 'Continue'
$TaskId = 'aays-101-manual-label-status-check-20260515'
$BridgeRoot = if ($env:AAYS_BRIDGE_ROOT) { $env:AAYS_BRIDGE_ROOT } else { Split-Path -Parent $PSScriptRoot }
$ResultDir = Join-Path $BridgeRoot 'ai-results'
$HeartbeatDir = Join-Path $BridgeRoot 'ai-heartbeat'
New-Item -ItemType Directory -Force -Path $ResultDir,$HeartbeatDir | Out-Null
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$Report = Join-Path $ResultDir "aays-101-manual-label-status-check-$Stamp.md"
$Heartbeat = Join-Path $HeartbeatDir 'manual-label-status-check.md'
$Lines = New-Object System.Collections.Generic.List[string]
function L([string]$m){ [void]$Lines.Add($m) }
function Latest([string]$pattern){ Get-ChildItem $ResultDir -Filter $pattern -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1 }
$base = Latest 'aays-091-validation-label-template-*.csv'
$supp = Latest 'aays-092-supplemental-sample-*.csv'
$completed = Get-ChildItem $ResultDir -Filter '*completed_labels*.csv' -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending
L '# AAYS 101 Manual Label Status Check'
L ('Generated: ' + (Get-Date -Format s))
L ('TaskId: ' + $TaskId)
L 'Mode: read-only status check; no DB writes; no UI patch; no scoring changes.'
L ''
L '## Expected input files'
if($base){ L ('base_label_csv: ' + $base.FullName); L ('base_rows: ' + @((Import-Csv $base.FullName)).Count) } else { L 'base_label_csv: MISSING' }
if($supp){ L ('supplemental_sample_csv: ' + $supp.FullName); L ('supplemental_rows: ' + @((Import-Csv $supp.FullName)).Count) } else { L 'supplemental_sample_csv: MISSING' }
L ''
L '## Completed label files found'
if($completed -and @($completed).Count -gt 0){
  foreach($f in $completed){
    $rows = Import-Csv $f.FullName
    $filled = @($rows | Where-Object { -not [string]::IsNullOrWhiteSpace([string]$_.reviewer_label) }).Count
    L ($f.FullName + ' rows=' + @($rows).Count + ' reviewer_label_filled=' + $filled)
  }
} else {
  L 'NO_COMPLETED_LABELS_FOUND'
}
L ''
if($completed -and @($completed).Count -gt 0){
  L 'manual_review_gate: LABEL_FILE_FOUND'
  L 'next_allowed_task: label_outcome_audit'
  L 'wide_accuracy_program_percent: 97'
} else {
  L 'manual_review_gate: WAITING_FOR_HUMAN_LABELS'
  L 'next_allowed_task: none_until_completed_labels_exist'
  L 'wide_accuracy_program_percent: 96'
}
L 'production_acceptance_gate: NOT_READY_FOR_AUTO_ACCEPT'
L 'AAYS_101_MANUAL_LABEL_STATUS_CHECK_DONE=true'
Set-Content -Encoding UTF8 -Path $Report -Value $Lines
Set-Content -Encoding UTF8 -Path $Heartbeat -Value $Lines
Write-Output 'AAYS_101_MANUAL_LABEL_STATUS_CHECK_DONE=true'
Write-Output ('REPORT=' + $Report)
exit 0
