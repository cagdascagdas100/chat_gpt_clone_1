$ErrorActionPreference = 'Continue'
$TaskId = 'aays-091-validation-label-template-20260515'
$BridgeRoot = if ($env:AAYS_BRIDGE_ROOT) { $env:AAYS_BRIDGE_ROOT } else { Split-Path -Parent $PSScriptRoot }
$ResultDir = Join-Path $BridgeRoot 'ai-results'
$HeartbeatDir = Join-Path $BridgeRoot 'ai-heartbeat'
New-Item -ItemType Directory -Force -Path $ResultDir,$HeartbeatDir | Out-Null
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$Report = Join-Path $ResultDir "aays-091-validation-label-template-$Stamp.md"
$OutCsv = Join-Path $ResultDir "aays-091-validation-label-template-$Stamp.csv"
$Heartbeat = Join-Path $HeartbeatDir 'validation-label-template.md'
$SourceCsv = 'E:\AAYS_DATA\land_sales\final_outputs\stg_land_sales_50step_db_ready.csv'
$Lines = New-Object System.Collections.Generic.List[string]
function L([string]$m){ [void]$Lines.Add($m) }
L '# AAYS 091 Validation Label Template'
L ('Generated: ' + (Get-Date -Format s))
L ('TaskId: ' + $TaskId)
L ('SourceCsv: ' + $SourceCsv)
L 'Mode: read-only label template generation; no DB writes; no UI patch.'
if(!(Test-Path $SourceCsv)){
  L 'ERROR: source csv missing'
  Set-Content -Encoding UTF8 -Path $Report -Value $Lines
  exit 2
}
$rows = Import-Csv -Path $SourceCsv
$sample = @()
$sample += $rows | Where-Object { $_.geometry_verdict -eq 'derived_multi_signal' } | Select-Object -First 5
$sample += $rows | Where-Object { $_.geometry_verdict -eq 'derived_signal' } | Select-Object -First 8
$sample += $rows | Where-Object { $_.geometry_verdict -eq 'derived_ai_visual' } | Select-Object -First 12
$sample = $sample | Select-Object -First 25
$i = 1
$template = foreach($r in $sample){
  [pscustomobject]@{
    validation_case_id = ('VS-' + $i.ToString('000'))
    verification_id = $r.verification_id
    listing_id = $r.listing_id
    geometry_verdict = $r.geometry_verdict
    geometry_evidence_type = $r.geometry_evidence_type
    geometry_uncertainty_m = $r.geometry_uncertainty_m
    postcode_standardized = $r.postcode_standardized
    local_authority_standardized = $r.local_authority_standardized
    ask_price = $r.ask_price
    normalized_area_m2 = $r.normalized_area_m2
    reviewer_label = ''
    reviewer_confidence = ''
    evidence_checked = ''
    issue_type = ''
    corrected_verdict = ''
    reviewer_notes = ''
  }
  $i++
}
$template | Export-Csv -NoTypeInformation -Encoding UTF8 -Path $OutCsv
L ('source_rows: ' + $rows.Count)
L ('template_rows: ' + @($template).Count)
L ('label_csv: ' + $OutCsv)
L ''
L '## Allowed reviewer_label values'
L 'accept, downgrade, reject, needs_source, ambiguous'
L ''
L '## Allowed issue_type values'
L 'none, missing_source, postcode_mismatch, authority_mismatch, geometry_unsupported, area_outlier, price_outlier, ambiguous_candidate, other'
L ''
L '## Review instructions'
L '1. Fill reviewer_label for every row.'
L '2. Fill reviewer_confidence as high, medium, or low.'
L '3. Fill evidence_checked with yes/no.'
L '4. Use corrected_verdict only when label is downgrade or reject.'
L '5. Do not change thresholds until all 25 rows are labeled.'
L ''
L '## Template preview'
L ($template | Select-Object -First 10 | Format-Table -AutoSize | Out-String)
L ''
L 'wide_accuracy_program_percent: 60'
L 'AAYS_091_VALIDATION_LABEL_TEMPLATE_DONE=true'
Set-Content -Encoding UTF8 -Path $Report -Value $Lines
Set-Content -Encoding UTF8 -Path $Heartbeat -Value $Lines
Write-Output 'AAYS_091_VALIDATION_LABEL_TEMPLATE_DONE=true'
Write-Output ('REPORT=' + $Report)
Write-Output ('LABEL_CSV=' + $OutCsv)
exit 0
