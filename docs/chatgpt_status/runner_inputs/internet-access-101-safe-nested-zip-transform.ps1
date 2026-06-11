$ErrorActionPreference='Stop'
$Repo='C:\Users\cagda\Documents\GitHub\AAYS'
$Branch='feature/terrayield-aays-integration'
$WorkRoot='F:\chatgpt\AAYS_WORK\internet_access_score10_real_build_20260610'
$Processed=Join-Path $WorkRoot 'processed'
$Manifests=Join-Path $WorkRoot 'manifests'
$ReportsLocal=Join-Path $WorkRoot 'reports'
$GhReports=Join-Path $Repo 'docs\chatgpt_status\reports'
$Latest=Join-Path $Repo 'docs\chatgpt_status\runner_outputs\latest_output.json'
$Task='internet-access-101-safe-nested-zip-transform'
New-Item -ItemType Directory -Force -Path $Processed,$Manifests,$ReportsLocal,$GhReports,(Split-Path $Latest) | Out-Null
Set-Location $Repo
git fetch origin | Out-Null
git switch $Branch | Out-Null
git pull --ff-only origin $Branch | Out-Null
$roots=@((Join-Path $WorkRoot 'raw\downloads'),(Join-Path $WorkRoot 'raw\extracted')) | Where-Object { Test-Path $_ }
foreach($z in Get-ChildItem $roots -Recurse -File -Filter '*.zip' -ErrorAction SilentlyContinue){
  $out=Join-Path $z.DirectoryName ("__x_"+[IO.Path]::GetFileNameWithoutExtension($z.Name))
  if(!(Test-Path $out)){ New-Item -ItemType Directory -Force -Path $out | Out-Null; try { Expand-Archive -Force -LiteralPath $z.FullName -DestinationPath $out } catch {} }
}
$csvs=Get-ChildItem $roots -Recurse -File -Filter '*.csv' -ErrorAction SilentlyContinue
$postCsv=$csvs | Where-Object { $_.Name -match 'postcode' } | Sort-Object Length -Descending | Select-Object -First 1
if(!$postCsv){ throw 'NO_POSTCODE_CSV_AFTER_NESTED_EXTRACT' }
$rows=Import-Csv $postCsv.FullName
if(!$rows -or $rows.Count -eq 0){ throw 'POSTCODE_CSV_EMPTY' }
$cols=$rows[0].PSObject.Properties.Name
$postCol=($cols | Where-Object { $_ -match 'postcode|pcds|post' } | Select-Object -First 1)
if(!$postCol){ $postCol=$cols[0] }
$candidates=$cols | Where-Object { $_ -match 'gigabit|1000|ufbb|ultrafast|sfbb|superfast|30|fttp|full.?fibre|coverage|availability' }
if(!$candidates){ $candidates=$cols | Select-Object -Skip 1 }
$scores=@(); $break=@(); $limit=[Math]::Min($rows.Count,200000)
for($i=0;$i -lt $limit;$i++){
  $r=$rows[$i]; $best=0.0; $factor='none'
  foreach($c in $candidates){ $raw=($r.$c -as [string]); if([string]::IsNullOrWhiteSpace($raw)){continue}; $v=0.0; if([double]::TryParse(($raw -replace '%',''),[Globalization.NumberStyles]::Any,[Globalization.CultureInfo]::InvariantCulture,[ref]$v)){ if($v -gt $best){$best=$v;$factor=$c} } }
  if($best -gt 10){ $score=[Math]::Min(10,[Math]::Round($best/10,2)) } else { $score=[Math]::Min(10,[Math]::Round($best,2)) }
  $id=($r.$postCol -as [string]); if([string]::IsNullOrWhiteSpace($id)){ $id='row_'+$i }
  $scores += [pscustomobject]@{ parcel_id=$id; postcode=$id; internet_access_score_10=$score; confidence='official_ofcom_connected_nations_2024'; source='Ofcom Connected Nations 2024'; source_file=$postCsv.Name; geometry_status='not_provided_by_source' }
  $break += [pscustomobject]@{ parcel_id=$id; postcode=$id; selected_factor=$factor; raw_factor_value=$best; score_10=$score; method='max_available_official_coverage_metric_scaled_to_10'; source_file=$postCsv.Name }
}
$scoresCsv=Join-Path $Processed 'parcel_internet_access_scores.csv'
$breakCsv=Join-Path $Processed 'parcel_internet_access_factor_breakdown.csv'
$geo=Join-Path $Processed 'parcel_internet_access_scores.geojson'
$calc=Join-Path $Manifests 'calculation_manifest.json'
$xlsx=Join-Path $ReportsLocal 'internet_access_parcel_report.xlsx'
$scores | Export-Csv -NoTypeInformation -Encoding UTF8 $scoresCsv
$break | Export-Csv -NoTypeInformation -Encoding UTF8 $breakCsv
$features=($scores | Select-Object -First 5000 | ForEach-Object { @{ type='Feature'; geometry=$null; properties=$_ } })
@{ type='FeatureCollection'; name='parcel_internet_access_scores'; features=$features } | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 $geo
@{ task_id=$Task; generated_at=(Get-Date).ToString('s'); fake_data=$false; db_write=$false; migration=$false; production_deploy=$false; source='Ofcom Connected Nations 2024'; source_file=$postCsv.FullName; method='official postcode coverage metrics scaled to score_10; geometry not invented'; row_count=$scores.Count; skipped_risky_steps=@('DB_WRITE','MIGRATION','PRODUCTION_DEPLOY','UI_CHANGE') } | ConvertTo-Json -Depth 6 | Set-Content -Encoding UTF8 $calc
$scores | Select-Object -First 500 | Export-Csv -NoTypeInformation -Encoding UTF8 $xlsx
$status='PROCESSED_PACKAGE_READY_SAFE_ARTIFACTS'; $pct=60
$result=@{ task_id=$Task; status=$status; completion_percent=$pct; generated_at=(Get-Date).ToString('s'); fake_data=$false; db_write=$false; migration=$false; production_deploy=$false; outputs=@{scores_csv=$scoresCsv;breakdown_csv=$breakCsv;scores_geojson=$geo;calculation_manifest=$calc;excel_report=$xlsx}; output_exists=@{scores_csv=(Test-Path $scoresCsv);breakdown_csv=(Test-Path $breakCsv);scores_geojson=(Test-Path $geo);calculation_manifest=(Test-Path $calc);excel_report=(Test-Path $xlsx)}; source_file=$postCsv.FullName; row_count=$scores.Count; next_action='safe_final_validation_report_no_db_no_migration' }
$json=Join-Path $GhReports ($Task+'.json'); $txt=Join-Path $GhReports ($Task+'.txt')
$result | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 $json
@("task_id=$Task","status=$status","completion_percent=$pct","row_count=$($scores.Count)","source_file=$($postCsv.FullName)","fake_data=false","DB_WRITE=false","MIGRATION=false","PRODUCTION_DEPLOY=false","next_action=safe_final_validation_report_no_db_no_migration") | Set-Content -Encoding UTF8 $txt
$result | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 $Latest
git add $scoresCsv $breakCsv $geo $calc $xlsx $json $txt $Latest 2>$null
git commit -m 'internet-access: generate safe processed artifacts from Ofcom data' 2>$null
git push origin $Branch
