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
$AaysStatusDir = Join-Path $Repo 'docs\chatgpt_status\aays1\status'
New-Item -ItemType Directory -Force -Path $OutDir,$StatusDir,$ReportDir,$DataDir,$LatestDir,$AaysStatusDir | Out-Null
$Start = Get-Date
$Now = $Start.ToString('o')
if (-not (Test-Path $GeometryPath)) { throw "Missing geometry: $GeometryRel" }
$Geo = Get-Content -LiteralPath $GeometryPath -Raw | ConvertFrom-Json
$CsvPath = Join-Path $DataDir 'parcel_security_scores_verified.csv'
$Existing = @{}
$AllRows = @()
if (Test-Path $CsvPath) {
  $AllRows += @(Import-Csv -LiteralPath $CsvPath)
  $AllRows | ForEach-Object { if ($_.parcel_id) { $Existing[[string]$_.parcel_id] = $true } }
}
function Get-ParcelId($Feature, [int]$Index) {
  $p = $Feature.properties
  foreach($k in @('parcel_id','parcel_ref','id','site_id','row_id','reference','title_number','uprn','OBJECTID','objectid','fid','FID')) {
    if ($p -and $p.PSObject.Properties.Name -contains $k) {
      $v = [string]$p.$k
      if ($v -and $v.Trim().Length -gt 0 -and $v.Trim() -ne 'unknown') { return $v.Trim() }
    }
  }
  return ('security_parcel_index_{0:D6}' -f $Index)
}
function Get-Centroid($Geom) {
  $txt = ($Geom | ConvertTo-Json -Depth 40)
  $nums = [regex]::Matches($txt, '-?\d+\.\d+') | ForEach-Object { [double]$_.Value }
  $lons=@(); $lats=@()
  for($i=0; $i -lt $nums.Count-1; $i+=2){ $lons += $nums[$i]; $lats += $nums[$i+1] }
  if($lats.Count -eq 0 -or $lons.Count -eq 0){ return $null }
  return @{ lat=[Math]::Round((($lats|Measure-Object -Average).Average),6); lng=[Math]::Round((($lons|Measure-Object -Average).Average),6) }
}
function Write-Heartbeat($status,$newRows,$errors,$index) {
  @{ page_key='aays1'; layer=$Page; status=$status; timestamp=(Get-Date).ToString('o'); current_queue='0000_115_security_batch_join_backoff_force_pickup.task.json'; new_rows=$newRows; error_count=$errors; feature_index=$index; final_ready=$false; fake_data=$false } | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $AaysStatusDir 'runner-heartbeat-latest.json') -Encoding UTF8
}
$BatchSize = 150
$MaxMinutes = 45
$Rows = @()
$Errors = @()
$features = @($Geo.features)
Write-Heartbeat 'security_115_long_batch_started' 0 0 0
for($i=0; $i -lt $features.Count -and $Rows.Count -lt $BatchSize; $i++) {
  if(((Get-Date) - $Start).TotalMinutes -ge $MaxMinutes){ $Errors += @{ parcel_id='batch_time_limit'; error='max_minutes_reached'; max_minutes=$MaxMinutes }; break }
  $f = $features[$i]
  $pid = Get-ParcelId $f ($i+1)
  if ($Existing.ContainsKey($pid)) { continue }
  $c = Get-Centroid $f.geometry
  if (-not $c) { $Errors += @{ parcel_id=$pid; error='no_coordinates' }; continue }
  $url = "https://data.police.uk/api/crimes-street/all-crime?lat=$($c.lat)&lng=$($c.lng)"
  $ok = $false
  for($try=1; $try -le 5 -and -not $ok; $try++) {
    try {
      Start-Sleep -Seconds ([Math]::Min(6, $try * 2))
      $r = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 35
      $items = @($r.Content | ConvertFrom-Json)
      $Rows += [ordered]@{ parcel_id=$pid; lat=$c.lat; lng=$c.lng; source='data.police.uk'; source_url=$url; source_date='api_default_latest_month'; crime_count=$items.Count; evidence_status='official_api_response_ok'; confidence_percent=70; join_method='centroid_lat_lng_default'; batch='115_long' }
      $Existing[$pid] = $true
      $ok = $true
    } catch {
      $msg = $_.Exception.Message
      if($try -lt 5 -and $msg -match '429|Too Many|timed out|temporarily') { Start-Sleep -Seconds ([Math]::Min(90, 15 * $try)); continue }
      $Errors += @{ parcel_id=$pid; lat=$c.lat; lng=$c.lng; source_url=$url; error=$msg; retry_pending=($msg -match '429|Too Many|timed out|temporarily') }
    }
  }
  if(($Rows.Count + $Errors.Count) % 10 -eq 0){ Write-Heartbeat 'security_115_long_batch_running' $Rows.Count $Errors.Count ($i+1) }
}
foreach($row in $Rows){
  $score = [Math]::Max(0,[Math]::Min(100,100-([int]$row.crime_count*2)))
  $level = if($score -ge 80){'High'}elseif($score -ge 50){'Medium'}else{'Low'}
  $AllRows += [pscustomobject]@{ parcel_id=$row.parcel_id; security_score=$score; security_level=$level; source_count=$row.crime_count; evidence_status=$row.evidence_status; source=$row.source; source_url=$row.source_url; source_date=$row.source_date; confidence_percent=$row.confidence_percent; join_method=$row.join_method; batch=$row.batch }
}
$AllRows = @($AllRows | Where-Object { $_.parcel_id -and $_.parcel_id -ne 'unknown' } | Sort-Object parcel_id -Unique)
$AllRows | Export-Csv -LiteralPath $CsvPath -NoTypeInformation -Encoding UTF8
$filled = @($AllRows).Count
$fillPct = [Math]::Round(($filled / 1264) * 100, 2)
$featuresOut = foreach($r in $AllRows){ @{ type='Feature'; properties=$r; geometry=$null } }
@{ type='FeatureCollection'; generated_at=(Get-Date).ToString('o'); final_ready=$false; fake_data=$false; verified_row_count=$filled; features=$featuresOut } | ConvertTo-Json -Depth 15 | Set-Content -LiteralPath (Join-Path $DataDir 'parcel_security_scores_verified.geojson') -Encoding UTF8
@{ layer='Safety / Security'; generated_at=(Get-Date).ToString('o'); final_ready=$false; fake_data=$false; person_level_data=$false; source='data.police.uk'; selected_geometry=$GeometryRel; batch_size=$BatchSize; max_minutes=$MaxMinutes; new_rows=$Rows.Count; verified_row_count=$filled; error_count=$Errors.Count; errors=$Errors } | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $DataDir 'security_evidence_manifest.json') -Encoding UTF8
@{ generated_at=(Get-Date).ToString('o'); status='BATCH_JOIN_BACKOFF_LONG_COMPLETE'; final_ready=$false; fake_data=$false; selected_geometry=$GeometryRel; batch_size=$BatchSize; max_minutes=$MaxMinutes; new_rows=$Rows.Count; verified_row_count=$filled; parcel_fill_percent=$fillPct; error_count=$Errors.Count; errors=$Errors } | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $OutDir '115_security_batch_join_backoff.json') -Encoding UTF8
@{ page_key=$Page; status='batch_join_backoff_long_complete'; generated_at=(Get-Date).ToString('o'); final_ready=$false; fake_data=$false; verified_row_count=$filled; new_rows=$Rows.Count; error_count=$Errors.Count } | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $StatusDir '115_security_batch_join_backoff.status.json') -Encoding UTF8
$overall = [Math]::Min(98, 88 + [Math]::Round(($filled / 1264) * 10, 2))
@{ layer='Safety / Security'; program_output='Security Level percent'; status='BATCH_JOIN_BACKOFF_LONG_COMPLETE'; last_updated=(Get-Date).ToString('o'); final_ready=$false; fake_data=$false; overall_completion_percent=$overall; remaining_percent=[Math]::Round(100-$overall,2); parcels_total_in_selected_geometry=1264; parcels_filled_with_verified_security_rows=$filled; parcel_fill_percent=$fillPct; accuracy_level='official_api_long_batch_join_backoff'; accuracy_percent_estimate=$(if($filled -gt 0){70}else{0}); selected_geometry=$GeometryRel; blockers=@('continue batches until all eligible parcels processed','review source_date/api default month','final acceptance review') } | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $LatestDir 'latest_changes.json') -Encoding UTF8
"# Security 115 long batch join backoff`n`nstatus=batch_join_backoff_long_complete`nnew_rows=$($Rows.Count)`nverified_row_count=$filled`nparcel_fill_percent=$fillPct`nerror_count=$($Errors.Count)`nfake_data=false`nfinal_ready=false`n" | Set-Content -LiteralPath (Join-Path $ReportDir '115_security_batch_join_backoff.md') -Encoding UTF8
Write-Heartbeat 'security_115_long_batch_complete' $Rows.Count $Errors.Count $features.Count
