$ErrorActionPreference = 'Continue'
$TaskId = 'aays-088-validation-sample-20260515'
$BridgeRoot = if ($env:AAYS_BRIDGE_ROOT) { $env:AAYS_BRIDGE_ROOT } else { Split-Path -Parent $PSScriptRoot }
$DataRoot = 'E:\AAYS_DATA\land_sales'
$ResultDir = Join-Path $BridgeRoot 'ai-results'
$HeartbeatDir = Join-Path $BridgeRoot 'ai-heartbeat'
New-Item -ItemType Directory -Force -Path $ResultDir,$HeartbeatDir | Out-Null
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$Report = Join-Path $ResultDir "aays-088-validation-sample-$Stamp.md"
$Heartbeat = Join-Path $HeartbeatDir 'validation-sample.md'
$Csv = Join-Path $DataRoot 'final_outputs\stg_land_sales_50step_db_ready.csv'
$Lines = New-Object System.Collections.Generic.List[string]
function AddLine([string]$m){ [void]$Lines.Add($m) }
AddLine '# AAYS 088 Validation Sample'
AddLine ('Generated: ' + (Get-Date -Format s))
AddLine ('TaskId: ' + $TaskId)
AddLine ('Csv: ' + $Csv)
AddLine 'Mode: read-only validation sample; no DB writes; no UI patch.'
if(!(Test-Path $Csv)){
  AddLine 'ERROR: CSV missing'
  Set-Content -Encoding UTF8 -Path $Report -Value $Lines
  Set-Content -Encoding UTF8 -Path $Heartbeat -Value $Lines
  exit 2
}
try {
  $rows = Import-Csv -Path $Csv
  AddLine ('total_rows: ' + $rows.Count)
  AddLine ''
  AddLine '## Verdict distribution'
  $rows | Group-Object geometry_verdict | Sort-Object Count -Descending | ForEach-Object { AddLine ($_.Name + ': ' + $_.Count) }
  AddLine ''
  AddLine '## Evidence type distribution'
  $rows | Group-Object geometry_evidence_type | Sort-Object Count -Descending | Select-Object -First 20 | ForEach-Object { AddLine ($_.Name + ': ' + $_.Count) }
  AddLine ''
  AddLine '## Validation sample candidates'
  AddLine 'Columns: verification_id | listing_id | verdict | evidence | uncertainty_m | postcode | authority | price | area'
  $sample = @()
  $sample += $rows | Where-Object { $_.geometry_verdict -eq 'derived_multi_signal' } | Select-Object -First 5
  $sample += $rows | Where-Object { $_.geometry_verdict -eq 'derived_signal' } | Select-Object -First 8
  $sample += $rows | Where-Object { $_.geometry_verdict -eq 'derived_ai_visual' } | Select-Object -First 12
  $sample = $sample | Select-Object -First 25
  foreach($r in $sample){
    AddLine (($r.verification_id) + ' | ' + ($r.listing_id) + ' | ' + ($r.geometry_verdict) + ' | ' + ($r.geometry_evidence_type) + ' | ' + ($r.geometry_uncertainty_m) + ' | ' + ($r.postcode_standardized) + ' | ' + ($r.local_authority_standardized) + ' | ' + ($r.ask_price) + ' | ' + ($r.normalized_area_m2))
  }
  AddLine ''
  AddLine '## Next manual validation rubric'
  AddLine '1. For each sample row, open listing_url_canonical/source_urls_json.'
  AddLine '2. Verify postcode/local authority normalization against authoritative source.'
  AddLine '3. Check whether geometry_verdict is supported by evidence type and uncertainty.'
  AddLine '4. Mark expected outcome: accept, downgrade, reject, needs_source.'
  AddLine '5. Use at least 25 rows before changing scoring thresholds.'
  AddLine ''
  AddLine 'wide_accuracy_program_percent: 45'
  AddLine 'AAYS_088_VALIDATION_SAMPLE_DONE=true'
} catch {
  AddLine ('ERROR: ' + $_.Exception.Message)
}
Set-Content -Encoding UTF8 -Path $Report -Value $Lines
Set-Content -Encoding UTF8 -Path $Heartbeat -Value $Lines
Write-Output 'AAYS_088_VALIDATION_SAMPLE_DONE=true'
Write-Output ('REPORT=' + $Report)
exit 0
