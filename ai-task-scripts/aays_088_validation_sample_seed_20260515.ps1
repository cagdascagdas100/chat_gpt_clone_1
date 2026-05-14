$ErrorActionPreference = 'Continue'
$TaskId = 'aays-088-validation-sample-seed-20260515'
$BridgeRoot = if ($env:AAYS_BRIDGE_ROOT) { $env:AAYS_BRIDGE_ROOT } else { Split-Path -Parent $PSScriptRoot }
$ResultDir = Join-Path $BridgeRoot 'ai-results'
$HeartbeatDir = Join-Path $BridgeRoot 'ai-heartbeat'
New-Item -ItemType Directory -Force -Path $ResultDir,$HeartbeatDir | Out-Null
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$Report = Join-Path $ResultDir "aays-088-validation-sample-seed-$Stamp.md"
$SeedCsv = Join-Path $ResultDir "aays-088-validation-sample-seed-$Stamp.csv"
$Heartbeat = Join-Path $HeartbeatDir 'validation-sample-seed.md'
$Csv = 'E:\AAYS_DATA\land_sales\final_outputs\stg_land_sales_50step_db_ready.csv'
$Lines = New-Object System.Collections.Generic.List[string]
function L([string]$m){ [void]$Lines.Add($m) }
L '# AAYS 088 Validation Sample Seed'
L ('Generated: ' + (Get-Date -Format s))
L ('TaskId: ' + $TaskId)
L ('Csv: ' + $Csv)
L 'Mode: read-only sample seed; no DB writes; no UI patch.'
if(!(Test-Path $Csv)){ L 'ERROR: source csv missing'; Set-Content -Encoding UTF8 -Path $Report -Value $Lines; exit 2 }
$rows = Import-Csv $Csv
$total = @($rows).Count
L ('total_rows: ' + $total)
$groups = $rows | Group-Object geometry_verdict | Sort-Object Count -Descending
L ''
L '## Geometry verdict distribution'
foreach($g in $groups){ L ($g.Name + ': ' + $g.Count) }
$sample = New-Object System.Collections.Generic.List[object]
$caseNo = 1
foreach($name in @('derived_multi_signal','derived_signal','derived_ai_visual')){
  $take = if($name -eq 'derived_ai_visual'){ 8 } else { 6 }
  $rows | Where-Object { $_.geometry_verdict -eq $name } | Select-Object -First $take | ForEach-Object {
    $sample.Add([pscustomobject]@{
      validation_case_id = ('VS-' + $caseNo.ToString('000'))
      listing_id = $_.listing_id
      verification_id = $_.verification_id
      geometry_verdict = $_.geometry_verdict
      ask_price = $_.ask_price
      normalized_area_m2 = $_.normalized_area_m2
      postcode_standardized = $_.postcode_standardized
      local_authority_standardized = $_.local_authority_standardized
      expected_review_action = 'manual_review_required'
      reviewer_note = 'Seed sample: confirm source evidence, geometry reasoning, and parcel linkage.'
    })
    $caseNo++
  }
}
$sample | Export-Csv -NoTypeInformation -Encoding UTF8 -Path $SeedCsv
L ''
L ('sample_rows: ' + $sample.Count)
L ('sample_csv: ' + $SeedCsv)
L ''
L '## Sample preview'
L ($sample | Select-Object -First 20 | Format-Table -AutoSize | Out-String)
L ''
L '## Next gates'
L 'gate_1_source_inventory: done'
L 'gate_2_schema_map: partial_from_headers_and_schema'
L 'gate_3_validation_sample: seed_done'
L 'gate_4_manual_labeling_protocol: next'
L 'wide_accuracy_program_percent: 45'
L 'AAYS_088_VALIDATION_SAMPLE_SEED_DONE=true'
Set-Content -Encoding UTF8 -Path $Report -Value $Lines
Set-Content -Encoding UTF8 -Path $Heartbeat -Value $Lines
Write-Output 'AAYS_088_VALIDATION_SAMPLE_SEED_DONE=true'
Write-Output ('REPORT=' + $Report)
Write-Output ('SEED_CSV=' + $SeedCsv)
exit 0
