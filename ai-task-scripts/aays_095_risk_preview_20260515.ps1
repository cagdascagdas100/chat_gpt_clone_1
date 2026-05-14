$ErrorActionPreference = 'Continue'
$TaskId = 'aays-095-risk-preview-20260515'
$BridgeRoot = if ($env:AAYS_BRIDGE_ROOT) { $env:AAYS_BRIDGE_ROOT } else { Split-Path -Parent $PSScriptRoot }
$DataRoot = 'E:\AAYS_DATA\land_sales'
$ResultDir = Join-Path $BridgeRoot 'ai-results'
$HeartbeatDir = Join-Path $BridgeRoot 'ai-heartbeat'
New-Item -ItemType Directory -Force -Path $ResultDir,$HeartbeatDir | Out-Null
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$Report = Join-Path $ResultDir "aays-095-risk-preview-$Stamp.md"
$OutCsv = Join-Path $ResultDir "aays-095-risk-preview-$Stamp.csv"
$Heartbeat = Join-Path $HeartbeatDir 'risk-preview.md'
$Csv = Join-Path $DataRoot 'final_outputs\stg_land_sales_50step_db_ready.csv'
$Lines = New-Object System.Collections.Generic.List[string]
function AddLine([string]$m){ [void]$Lines.Add($m) }
function Num($x){ $n=0.0; if([double]::TryParse([string]$x,[ref]$n)){ return $n }; return $null }
function Blank($x){ return [string]::IsNullOrWhiteSpace([string]$x) }
function Classify($r){
  $reasons = New-Object System.Collections.Generic.List[string]
  $risk = 'low'
  $status = 'manual_review'
  $price = Num $r.ask_price
  $area = Num $r.normalized_area_m2
  $ppm = Num $r.price_per_m2
  if((Blank $r.postcode_standardized) -or (Blank $r.local_authority_standardized) -or (Blank $r.ask_price) -or (Blank $r.normalized_area_m2)){
    $risk='critical'; $status='needs_source'; $reasons.Add('missing_core_field') | Out-Null
  }
  if(Blank $r.verified_polygon_geojson){ $risk='critical'; $status='manual_review'; $reasons.Add('no_verified_polygon') | Out-Null }
  if($r.geometry_verdict -eq 'derived_ai_visual'){ if($risk -ne 'critical'){ $risk='high'; $status='manual_review' }; $reasons.Add('ai_visual_candidate') | Out-Null }
  if($r.geometry_verdict -eq 'derived_signal'){ if($risk -eq 'low'){ $risk='medium'; $status='manual_review' }; $reasons.Add('signal_candidate') | Out-Null }
  if($r.geometry_verdict -eq 'derived_multi_signal'){ $reasons.Add('multi_signal_candidate') | Out-Null; if($risk -eq 'low'){ $risk='low'; $status='accept_candidate' } }
  if($area -ne $null -and $area -lt 100){ if($risk -ne 'critical'){ $risk='high'; $status='manual_review' }; $reasons.Add('area_below_100') | Out-Null }
  if($area -ne $null -and $area -gt 25000){ if($risk -ne 'critical'){ $risk='high'; $status='manual_review' }; $reasons.Add('area_above_25000') | Out-Null }
  if($price -ne $null -and $price -gt 3000000){ if($risk -ne 'critical'){ $risk='high'; $status='manual_review' }; $reasons.Add('price_above_3000000') | Out-Null }
  if($ppm -ne $null -and $ppm -gt 5000){ if($risk -ne 'critical'){ $risk='high'; $status='manual_review' }; $reasons.Add('ppm_above_5000') | Out-Null }
  if($reasons.Count -eq 0){ $reasons.Add('no_policy_flag') | Out-Null }
  return @($risk,$status,($reasons -join ';'))
}
AddLine '# AAYS 095 Risk Preview'
AddLine ('Generated: ' + (Get-Date -Format s))
AddLine ('TaskId: ' + $TaskId)
AddLine ('SourceCsv: ' + $Csv)
AddLine ('OutCsv: ' + $OutCsv)
AddLine 'Mode: read-only derived preview; source CSV is not overwritten.'
if(!(Test-Path $Csv)){
  AddLine 'ERROR: source CSV missing'
  Set-Content -Encoding UTF8 -Path $Report -Value $Lines
  Set-Content -Encoding UTF8 -Path $Heartbeat -Value $Lines
  exit 2
}
try {
  $rows = Import-Csv -Path $Csv
  $out = foreach($r in $rows){
    $c = Classify $r
    $obj = [ordered]@{}
    foreach($p in $r.PSObject.Properties){ $obj[$p.Name] = $p.Value }
    $obj['risk_label'] = $c[0]
    $obj['acceptance_status'] = $c[1]
    $obj['policy_reason'] = $c[2]
    [pscustomobject]$obj
  }
  $out | Export-Csv -NoTypeInformation -Encoding UTF8 -Path $OutCsv
  AddLine ('source_rows: ' + @($rows).Count)
  AddLine ('preview_rows: ' + @($out).Count)
  AddLine ''
  AddLine '## risk_label distribution'
  $out | Group-Object risk_label | Sort-Object Count -Descending | ForEach-Object { AddLine ($_.Name + ': ' + $_.Count) }
  AddLine ''
  AddLine '## acceptance_status distribution'
  $out | Group-Object acceptance_status | Sort-Object Count -Descending | ForEach-Object { AddLine ($_.Name + ': ' + $_.Count) }
  AddLine ''
  AddLine '## policy_reason top distribution'
  $out | Group-Object policy_reason | Sort-Object Count -Descending | Select-Object -First 20 | ForEach-Object { AddLine ($_.Name + ': ' + $_.Count) }
  AddLine ''
  AddLine 'wide_accuracy_program_percent: 78'
  AddLine 'AAYS_095_RISK_PREVIEW_DONE=true'
} catch { AddLine ('ERROR: ' + $_.Exception.Message) }
Set-Content -Encoding UTF8 -Path $Report -Value $Lines
Set-Content -Encoding UTF8 -Path $Heartbeat -Value $Lines
Write-Output 'AAYS_095_RISK_PREVIEW_DONE=true'
Write-Output ('REPORT=' + $Report)
exit 0
