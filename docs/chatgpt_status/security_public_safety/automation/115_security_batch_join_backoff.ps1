$ErrorActionPreference = 'Stop'
$Repo = $env:AAYS_REPO_ROOT
if (-not $Repo) { $Repo = (git rev-parse --show-toplevel).Trim() }
$Page = 'security_public_safety'
$GeometryRel = 'docs\chatgpt_status\aays1\geometry_review_3of4\all_1264_real_geometry_3of4.geojson'
$GeometryPath = Join-Path $Repo $GeometryRel
$Base = Join-Path $Repo "docs\chatgpt_status\$Page"
$OutDir = Join-Path $Base 'runner_outputs'
$StatusDir = Join-Path $Base 'status'
$ReportDir = Join-Path $Base 'reports'
$DataDir = Join-Path $Repo 'england_map_web\data\security_public_safety'
$LatestDir = Join-Path $Repo 'outputs\england_program_parcel_matrix_20260629\security_public_safety_updates'
New-Item -ItemType Directory -Force -Path $OutDir,$StatusDir,$ReportDir,$DataDir,$LatestDir | Out-Null
$Now = (Get-Date).ToString('o')
if (-not (Test-Path $GeometryPath)) { throw "Missing geometry: $GeometryRel" }
$Geo = Get-Content -LiteralPath $GeometryPath -Raw | ConvertFrom-Json
$CsvPath = Join-Path $DataDir 'parcel_security_scores_verified.csv'
$Existing = @{}
if (Test-Path $CsvPath) {
  Import-Csv -LiteralPath $CsvPath | ForEach-Object { if ($_.parcel_id) { $Existing[$_.parcel_id] = $true } }
}
function Get-ParcelId($Feature, [int]$Index) {
  $p = $Feature.properties
  foreach($k in @('parcel_id','parcel_ref','id','site_id','row_id','reference','title_number','uprn','OBJECTID','fid','FID')) {
    if ($p.PSObject.Properties.Name -contains $k) {
      $v = [string]$p.$k
      if ($v -and $v.Trim().Length -gt 0) { return $v.Trim() }
    }
  }
  return ('security_parcel_index_{0:D6}' -f $Index)
}
function Get-Centroid($Geom) {
  $txt = ($Geom | ConvertTo-Json -Depth 30)
  $nums = [regex]::Matches($txt, '-?\d+\.\d+') | ForEach-Object { [double]$_.Value }
  $lons=@(); $lats=@()
  for($i=0; $i -lt $nums.Count-1; $i+=2){ $lons += $nums[$i]; $lats += $nums[$i+1] }
  if($lats.Count -eq 0 -or $lons.Count -eq 0){ return $null }
  return @{ lat=[Math]::Round((($lats|Measure-Object -Average).Average),6); lng=[Math]::Round((($lons|Measure-Object -Average).Average),6) }
}
$BatchSize = 25
$Rows = @()
$Errors = @()
$features = @($Geo.features)
for($i=0; $i -lt $features.Count -and $Rows.Count -lt $BatchSize; $i++) {
  $f = $features[$i]
  $pid = Get-ParcelId $f ($i+1)
  if ($Existing.ContainsKey($pid)) { continue }
  $c = Get-Centroid $f.geometry
  if (-not $c) { $Errors += @{ parcel_id=$pid; error='no_coordinates' }; continue }
  $url = "https://data.police.uk/api/crimes-street/all-crime?lat=$($c.lat)&lng=$($c.lng)"
  $ok = $false
  for($try=1; $try -le 4 -and -not $ok; $try++) {
    try {
      Start-Sleep -Seconds (2 * $try)
      $r = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 30
      $items = @($r.Content | ConvertFrom-Json)
      $Rows += [ordered]@{ parcel_id=$pid; lat=$c.lat; lng=$c.lng; source='data.police.uk'; source_url=$url; source_date='api_default_latest_month'; crime_count=$items.Count; evidence_status='official_api_response_ok'; confidence_percent=70; join_method='centroid_lat_lng_radius_default' }
      $ok = $true
    } catch {
      $msg = $_.Exception.Message
      if($try -lt 4 -and $msg -match '429|Too Many') { Start-Sleep -Seconds (15 * $try); continue }
      $Errors += @{ parcel_id=$pid; lat=$c.lat; lng=$c.lng; source_url=$url; error=$msg }
    }
  }
}
$AllRows = @()
if(Test-Path $CsvPath){ $AllRows += @(Import-Csv -LiteralPath $CsvPath) }
foreach($row in $Rows){
  $score = [Math]::Max(0,[Math]::Min(100,100-([int]$row.crime_count*2)))
  $level = if($score -ge 80){'High'}elseif($score -ge 50){'Medium'}else{'Low'}
  $AllRows += [pscustomobject]@{ parcel_id=$row.parcel_id; security_score=$score; security_level=$level; source_count=$row.crime_count; evidence_status=$row.evidence_status; source=$row.source; source_url=$row.source_url; source_date=$row.source_date; confidence_percent=$row.confidence_percent; join_method=$row.join_method }
}
$AllRows | Sort-Object parcel_id -Unique | Export-Csv -LiteralPath $CsvPath -NoTypeInformation -Encoding UTF8
$filled = @($AllRows | Where-Object { $_.parcel_id }).Count
$fillPct = [Math]::Round(($filled / 1264) * 100, 2)
$featuresOut = foreach($r in $AllRows){ @{ type='Feature'; properties=$r; geometry=$null } }
@{ type='FeatureCollection'; generated_at=$Now; final_ready=$false; fake_data=$false; verified_row_count=$filled; features=$featuresOut } | ConvertTo-Json -Depth 15 | Set-Content -LiteralPath (Join-Path $DataDir 'parcel_security_scores_verified.geojson') -Encoding UTF8
@{ layer='Safety / Security'; generated_at=$Now; final_ready=$false; fake_data=$false; person_level_data=$false; source='data.police.uk'; selected_geometry=$GeometryRel; batch_size=$BatchSize; new_rows=$Rows.Count; verified_row_count=$filled; error_count=$Errors.Count; errors=$Errors } | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $DataDir 'security_evidence_manifest.json') -Encoding UTF8
@{ generated_at=$Now; status='BATCH_JOIN_BACKOFF_COMPLETE'; final_ready=$false; fake_data=$false; selected_geometry=$GeometryRel; batch_size=$BatchSize; new_rows=$Rows.Count; verified_row_count=$filled; parcel_fill_percent=$fillPct; error_count=$Errors.Count; errors=$Errors } | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $OutDir '115_security_batch_join_backoff.json') -Encoding UTF8
@{ page_key=$Page; status='batch_join_backoff_complete'; generated_at=$Now; final_ready=$false; fake_data=$false; verified_row_count=$filled; new_rows=$Rows.Count } | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $StatusDir '115_security_batch_join_backoff.status.json') -Encoding UTF8
$overall = [Math]::Min(95, 88 + [Math]::Round(($filled / 1264) * 7, 2))
@{ layer='Safety / Security'; program_output='Security Level percent'; status='BATCH_JOIN_BACKOFF_COMPLETE'; last_updated=$Now; final_ready=$false; fake_data=$false; overall_completion_percent=$overall; remaining_percent=[Math]::Round(100-$overall,2); parcels_total_in_selected_geometry=1264; parcels_filled_with_verified_security_rows=$filled; parcel_fill_percent=$fillPct; accuracy_level='official_api_batch_join_backoff'; accuracy_percent_estimate=$(if($filled -gt 0){70}else{0}); selected_geometry=$GeometryRel; blockers=@('continue batches until all eligible parcels processed','review source_date/api default month','final acceptance review') } | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $LatestDir 'latest_changes.json') -Encoding UTF8
"# Security 115 batch join backoff`n`nstatus=batch_join_backoff_complete`nnew_rows=$($Rows.Count)`nverified_row_count=$filled`nparcel_fill_percent=$fillPct`nfake_data=false`nfinal_ready=false`n" | Set-Content -LiteralPath (Join-Path $ReportDir '115_security_batch_join_backoff.md') -Encoding UTF8
