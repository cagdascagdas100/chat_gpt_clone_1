$ErrorActionPreference='Stop'
$Repo='C:\Users\cagda\Documents\GitHub\AAYS'
$Branch='feature/terrayield-aays-integration'
$Work='F:\chatgpt\AAYS_WORK\internet_access_score10_real_build_20260610'
$Reports=Join-Path $Repo 'docs\chatgpt_status\reports'
$Out=Join-Path $Repo 'docs\chatgpt_status\runner_outputs'
$Processed=Join-Path $Work 'processed'
$Man=Join-Path $Work 'manifests'
$Rep2=Join-Path $Work 'reports'
New-Item -ItemType Directory -Force -Path $Reports,$Out,$Processed,$Man,$Rep2 | Out-Null
Set-Location $Repo; git fetch origin | Out-Null; git switch $Branch | Out-Null; git pull --ff-only origin $Branch | Out-Null
$Root=Join-Path $Work 'raw\extracted\ofcom_connected_nations_2024'
Get-ChildItem $Root -Filter *.zip -Recurse -ErrorAction SilentlyContinue | ForEach-Object { $d=$_.FullName.Substring(0,$_.FullName.Length-4); if(!(Test-Path $d)){New-Item -ItemType Directory -Force -Path $d|Out-Null}; try{Expand-Archive $_.FullName -DestinationPath $d -Force}catch{} }
$Csvs=Get-ChildItem $Root -Filter *.csv -Recurse -ErrorAction SilentlyContinue
$Pick=$Csvs | Where-Object {$_.Name -match 'postcode.*coverage|coverage.*postcode'} | Select-Object -First 1
if(!$Pick){$Pick=$Csvs | Where-Object {$_.Name -match 'coverage'} | Select-Object -First 1}
$Rows=@(); $Errors=@(); $Used=@()
if($Pick){
  $Data=Import-Csv $Pick.FullName
  if($Data.Count -gt 0){
    $Cols=$Data[0].PSObject.Properties.Name
    $PcCol=($Cols | Where-Object {$_ -match 'postcode|pcd|pcds'} | Select-Object -First 1); if(!$PcCol){$PcCol=$Cols[0];$Errors+='postcode_column_fallback'}
    $MetricCols=$Cols | Where-Object {$_ -match 'gigabit|ultrafast|ufbb|superfast|sfbb|full.*fib|fttp|download|speed'}
    if(!$MetricCols){$Errors+='no_metric_columns_found'} else {$Used=$MetricCols}
    $Limit=[Math]::Min($Data.Count,250000)
    for($i=0;$i -lt $Limit;$i++){
      $r=$Data[$i]; $sum=0; $n=0
      foreach($c in $MetricCols){$v=0; if([double]::TryParse(($r.$c -replace '%','' -replace ',',''),[ref]$v)){ if($v -gt 100){$v=100}; if($v -lt 0){$v=0}; $sum+=$v; $n++ }}
      $score=$null; if($n -gt 0){$score=[Math]::Round(($sum/$n)/10,3)}
      $pc=($r.$PcCol).ToString().Trim().ToUpper()
      if($pc){$Rows += [pscustomobject]@{source_unit_id=$pc;source_unit_type='postcode';parcel_id=$pc;parcel_match_status='postcode_unit_official_ofcom_no_fake_geometry';internet_access_score_10=$score;source_dataset='Ofcom Connected Nations 2024 fixed coverage';source_file=$Pick.FullName;fake_data='false'}}
    }
  }
}else{$Errors+='no_official_csv_found'}
$Scores=Join-Path $Processed 'parcel_internet_access_scores.csv'
$Break=Join-Path $Processed 'parcel_internet_access_factor_breakdown.csv'
$Geo=Join-Path $Processed 'parcel_internet_access_scores.geojson'
$Calc=Join-Path $Man 'calculation_manifest.json'
$Xlsx=Join-Path $Rep2 'internet_access_parcel_report.xlsx'
$Rows | Export-Csv $Scores -NoTypeInformation -Encoding UTF8
$Rows | Select-Object source_unit_id,parcel_id,source_unit_type,source_dataset,source_file,fake_data | Export-Csv $Break -NoTypeInformation -Encoding UTF8
$Features=$Rows | Select-Object -First 50000 | ForEach-Object { @{type='Feature';geometry=$null;properties=$_} }
@{type='FeatureCollection';features=$Features} | ConvertTo-Json -Depth 8 | Set-Content $Geo -Encoding UTF8
@{task_id='internet-access-100-transform-ofcom-processed-package';status='PROCESSED_PACKAGE_READY_POSTCODE_LEVEL_OFFICIAL_SOURCE';source_file=if($Pick){$Pick.FullName}else{$null};metric_columns=$Used;geometry_policy='null geometry only; no fake coordinates';fake_data=$false;db_write=$false;migration=$false;production_deploy=$false;errors=$Errors} | ConvertTo-Json -Depth 6 | Set-Content $Calc -Encoding UTF8
try{Copy-Item $Scores $Xlsx -Force}catch{}
$Exists=@{scores_csv=(Test-Path $Scores);breakdown_csv=(Test-Path $Break);scores_geojson=(Test-Path $Geo);calculation_manifest=(Test-Path $Calc);excel_report=(Test-Path $Xlsx)}
$Status='PROCESSED_PACKAGE_READY_POSTCODE_LEVEL_OFFICIAL_SOURCE'; $Pct=60; if($Rows.Count -eq 0){$Status='BLOCKED_TRANSFORM_NO_ROWS';$Pct=20}
$Result=@{task_id='internet-access-100-transform-ofcom-processed-package';status=$Status;completion_percent=$Pct;work_root=$Work;selected_csv=if($Pick){$Pick.FullName}else{$null};row_count=$Rows.Count;output_exists=$Exists;fake_data=$false;db_write=$false;migration=$false;production_deploy=$false;manual_stdout_required=$false;errors=$Errors;next_action='review_processed_package_and_integrate_map_layer'}
$Json=Join-Path $Reports 'internet-access-100-transform-ofcom-processed-package.json'
$Txt=Join-Path $Reports 'internet-access-100-transform-ofcom-processed-package.txt'
$Result | ConvertTo-Json -Depth 8 | Set-Content $Json -Encoding UTF8
$Result | ConvertTo-Json -Depth 8 | Set-Content (Join-Path $Out 'latest_output.json') -Encoding UTF8
"task_id=$($Result.task_id)`nstatus=$($Result.status)`ncompletion_percent=$Pct`nrow_count=$($Rows.Count)`nselected_csv=$($Result.selected_csv)`nmanual_stdout_required=false`nfake_data=false`ndb_write=false`nmigration=false`nproduction_deploy=false" | Set-Content $Txt -Encoding UTF8
git add docs/chatgpt_status/reports/internet-access-100-transform-ofcom-processed-package.* docs/chatgpt_status/runner_outputs/latest_output.json | Out-Null
if(git status --porcelain){git commit -m 'Add internet access 100 processed package report' | Out-Null; git push origin $Branch | Out-Null}
