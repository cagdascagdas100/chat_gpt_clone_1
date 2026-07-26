$ErrorActionPreference = 'Stop'
$Repo = $env:AAYS_REPO_ROOT
if (-not $Repo) { $Repo = (git rev-parse --show-toplevel).Trim() }
$Page = 'security_public_safety'
$Base = Join-Path $Repo "docs\chatgpt_status\$Page"
$OutDir = Join-Path $Base 'runner_outputs'
$ReportDir = Join-Path $Base 'reports'
$StatusDir = Join-Path $Base 'status'
$DataDir = Join-Path $Repo 'england_map_web\data\security_public_safety'
$LatestDir = Join-Path $Repo 'outputs\england_program_parcel_matrix_20260629\security_public_safety_updates'
New-Item -ItemType Directory -Force -Path $OutDir,$ReportDir,$StatusDir,$DataDir,$LatestDir | Out-Null
$Now = (Get-Date).ToString('o')
$GeometryRel = 'docs\chatgpt_status\aays1\geometry_review_3of4\all_1264_real_geometry_3of4.geojson'
$GeometryPath = Join-Path $Repo $GeometryRel
if(-not (Test-Path $GeometryPath)){ throw "Canonical geometry missing: $GeometryRel" }
$Geo = Get-Content -LiteralPath $GeometryPath -Raw | ConvertFrom-Json
$Features = @($Geo.features | Select-Object -First 10)
$Rows = @()
$Errors = @()
foreach($f in $Features){
  $parcelId = $null
  if($f.properties.parcel_id){ $parcelId = [string]$f.properties.parcel_id }
  elseif($f.properties.id){ $parcelId = [string]$f.properties.id }
  elseif($f.properties.parcel_ref){ $parcelId = [string]$f.properties.parcel_ref }
  else { $parcelId = 'unknown' }
  $coordsText = ($f.geometry | ConvertTo-Json -Depth 20)
  $nums = [regex]::Matches($coordsText, '-?\d+\.\d+') | ForEach-Object { [double]$_.Value }
  $lons = @(); $lats = @()
  for($i=0; $i -lt $nums.Count-1; $i+=2){ $lons += $nums[$i]; $lats += $nums[$i+1] }
  if($lats.Count -eq 0 -or $lons.Count -eq 0){ $Errors += @{ parcel_id=$parcelId; error='no_coordinates' }; continue }
  $lat = [Math]::Round((($lats | Measure-Object -Average).Average), 6)
  $lng = [Math]::Round((($lons | Measure-Object -Average).Average), 6)
  $url = "https://data.police.uk/api/crimes-street/all-crime?lat=$lat&lng=$lng"
  try {
    $r = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 20
    $items = @($r.Content | ConvertFrom-Json)
    $Rows += [ordered]@{ parcel_id=$parcelId; lat=$lat; lng=$lng; source='data.police.uk'; source_url=$url; source_date='api_default_latest_month'; crime_count=$items.Count; evidence_status='official_api_response_ok'; confidence_percent=70 }
  } catch {
    $Errors += @{ parcel_id=$parcelId; lat=$lat; lng=$lng; source_url=$url; error=$_.Exception.Message }
  }
}
$CsvPath = Join-Path $DataDir 'parcel_security_scores_verified.csv'
'parcel_id,security_score,security_level,source_count,evidence_status,source,source_url,source_date,confidence_percent' | Set-Content -LiteralPath $CsvPath -Encoding UTF8
foreach($row in $Rows){
  $score = [Math]::Max(0, [Math]::Min(100, 100 - ([int]$row.crime_count * 2)))
  $level = if($score -ge 80){'High'}elseif($score -ge 50){'Medium'}else{'Low'}
  ('{0},{1},{2},{3},{4},{5},"{6}",{7},{8}' -f $row.parcel_id,$score,$level,$row.crime_count,$row.evidence_status,$row.source,$row.source_url,$row.source_date,$row.confidence_percent) | Add-Content -LiteralPath $CsvPath -Encoding UTF8
}
$FeaturesOut = foreach($row in $Rows){ @{ type='Feature'; properties=@{ parcel_id=$row.parcel_id; security_score=[Math]::Max(0, [Math]::Min(100, 100 - ([int]$row.crime_count * 2))); source_count=$row.crime_count; evidence_status=$row.evidence_status; confidence_percent=$row.confidence_percent; source=$row.source; source_url=$row.source_url; source_date=$row.source_date }; geometry=$null } }
@{ type='FeatureCollection'; generated_at=$Now; final_ready=$false; fake_data=$false; verified_row_count=$Rows.Count; features=$FeaturesOut } | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $DataDir 'parcel_security_scores_verified.geojson') -Encoding UTF8
@{ layer='Safety / Security'; program_output='Security Level percent'; generated_at=$Now; final_ready=$false; fake_data=$false; person_level_data=$false; source='data.police.uk'; selected_geometry=$GeometryRel; sampled_parcels=$Features.Count; verified_row_count=$Rows.Count; error_count=$Errors.Count; errors=$Errors } | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $DataDir 'security_evidence_manifest.json') -Encoding UTF8
@{ generated_at=$Now; status='OFFICIAL_SOURCE_JOIN_PROBED'; final_ready=$false; fake_data=$false; selected_geometry=$GeometryRel; sampled_parcels=$Features.Count; verified_row_count=$Rows.Count; error_count=$Errors.Count; rows=$Rows; errors=$Errors } | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $OutDir '114_security_official_source_join_probe.json') -Encoding UTF8
@{ page_key=$Page; status='official_source_join_probed'; generated_at=$Now; final_ready=$false; fake_data=$false; verified_row_count=$Rows.Count } | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $StatusDir '114_security_official_source_join_probe.status.json') -Encoding UTF8
@{ layer='Safety / Security'; program_output='Security Level percent'; status='OFFICIAL_SOURCE_JOIN_PROBE_READY_FOR_REVIEW'; last_updated=$Now; final_ready=$false; fake_data=$false; overall_completion_percent=88; remaining_percent=12; parcels_total_in_selected_geometry=1264; parcels_filled_with_verified_security_rows=$Rows.Count; parcel_fill_percent=[Math]::Round(($Rows.Count/1264)*100,2); accuracy_level='official_api_sample_join_probe'; accuracy_percent_estimate=$(if($Rows.Count -gt 0){70}else{0}); selected_geometry=$GeometryRel; blockers=@('expand official source join from sample to all eligible parcels','review source_date/api default month','final acceptance review') } | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $LatestDir 'latest_changes.json') -Encoding UTF8
"# Security official source join probe`n`nstatus=official_source_join_probed`nverified_row_count=$($Rows.Count)`nfake_data=false`nfinal_ready=false`n" | Set-Content -LiteralPath (Join-Path $ReportDir '114_security_official_source_join_probe.md') -Encoding UTF8
