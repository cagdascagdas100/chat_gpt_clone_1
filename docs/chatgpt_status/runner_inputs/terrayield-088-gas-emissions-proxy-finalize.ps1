$ErrorActionPreference='Stop'
$Repo='C:\Users\cagda\Documents\GitHub\AAYS'
$Branch='feature/terrayield-aays-integration'
$WorkRoot='F:\chatgpt\AAYS_WORK\gas_emissions_proxy_finalize_20260612'
$ReportsLocal=Join-Path $WorkRoot 'reports'
$GhReports=Join-Path $Repo 'docs\chatgpt_status\reports'
$Latest=Join-Path $Repo 'docs\chatgpt_status\runner_outputs\latest_output.json'
$Task='terrayield-088-gas-emissions-proxy-finalize'
New-Item -ItemType Directory -Force -Path $WorkRoot,$ReportsLocal,$GhReports,(Split-Path $Latest) | Out-Null
Set-Location $Repo
git fetch origin | Out-Null
git switch $Branch | Out-Null
git pull --ff-only origin $Branch | Out-Null
$src=Join-Path $Repo 'england_map_web\data\parcel_air_quality_scores.geojson'
$out=Join-Path $Repo 'england_map_web\data\parcel_emissions_scores.geojson'
$csv=Join-Path $Repo 'england_map_web\data\parcel_emissions_scores.csv'
$manifest=Join-Path $Repo 'england_map_web\data\parcel_emissions_score_manifest.json'
$registry=Join-Path $Repo 'england_map_web\data\parcel_emissions_source_registry.csv'
$evidence=Join-Path $Repo 'england_map_web\data\parcel_emissions_evidence_manifest.jsonl'
if(!(Test-Path $src)){
  $result=@{task_id=$Task;status='BLOCKED_INPUT_MISSING';completion_percent=55;generated_at=(Get-Date).ToString('s');final_ready=$false;fake_data=$false;db_write=$false;migration=$false;production_deploy=$false;missing_input=$src;next_action='restore parcel_air_quality_scores.geojson and rerun'}
  $result|ConvertTo-Json -Depth 8|Set-Content -Encoding UTF8 (Join-Path $GhReports ($Task+'.json'))
  $result|ConvertTo-Json -Depth 8|Set-Content -Encoding UTF8 $Latest
  @('task_id='+$Task,'status=BLOCKED_INPUT_MISSING','completion_percent=55','final_ready=false','fake_data=false','DB_WRITE=false','MIGRATION=false','PRODUCTION_DEPLOY=false')|Set-Content -Encoding UTF8 (Join-Path $GhReports ($Task+'.txt'))
  git add docs/chatgpt_status/reports docs/chatgpt_status/runner_outputs 2>$null
  git commit -m 'gas-emissions: report missing proxy input' 2>$null
  git push origin $Branch
  exit 0
}
$geo=Get-Content -Raw -Encoding UTF8 $src|ConvertFrom-Json
function Val($o,$names){foreach($n in $names){if($o.PSObject.Properties.Name -contains $n){$v=$o.$n;if($null -ne $v -and (''+$v).Trim() -ne ''){return $v}}};return $null}
function Num($v){$d=0.0;if($null -ne $v -and [double]::TryParse((''+$v -replace '%',''),[Globalization.NumberStyles]::Any,[Globalization.CultureInfo]::InvariantCulture,[ref]$d)){return [Math]::Round([Math]::Max(0,[Math]::Min(100,$d)),2)};return $null}
function Level($p){if($p -le 20){return @('Cok Dusuk Emisyon','#2e7d32')};if($p -le 40){return @('Dusuk Emisyon','#8bc34a')};if($p -le 60){return @('Orta Emisyon','#fdd835')};if($p -le 80){return @('Yuksek Emisyon','#fb8c00')};return @('Cok Yuksek Emisyon','#c62828')}
$features=@();$rows=@();$ev=@();$skip=0;$i=0;$pointCount=0;$polygonCount=0;$multiPolygonCount=0
foreach($f in @($geo.features)){
  $i++
  if($null -eq $f.geometry -or @('Point','Polygon','MultiPolygon') -notcontains $f.geometry.type){$skip++;continue}
  if($f.geometry.type -eq 'Point'){$pointCount++}
  if($f.geometry.type -eq 'Polygon'){$polygonCount++}
  if($f.geometry.type -eq 'MultiPolygon'){$multiPolygonCount++}
  $p=$f.properties
  $pct=Num (Val $p @('pollutionRiskPercent','pollution_risk_percent','airQualityRiskPercent','risk_percent','score_percent'))
  if($null -eq $pct){$skip++;continue}
  $id=Val $p @('parcel_id','parcelId','id','parcel_ref','uprn')
  if($null -eq $id){$id='air_quality_proxy_'+$i}
  $lv=Level $pct
  $conf=Num (Val $p @('source_confidence','confidence_percent','confidencePercent','confidence','accuracy_percent'))
  $sd=Val $p @('source_date','last_source_update','last_update','updated_at')
  $sn=Val $p @('source_name','source','dataset','publisher')
  if($null -eq $sn){$sn='AAYS parcel_air_quality_scores.geojson'}
  $geomMode=if($f.geometry.type -eq 'Point'){'parcel_point_proxy'}else{'parcel_polygon_proxy'}
  $props=[ordered]@{parcel_id=(''+$id);parcel_ref=Val $p @('parcel_ref','parcelRef','reference','uprn');layer_name='Gas Emissions';gas_emission_percent=$pct;emission_percent=$pct;gas_emission_score=$pct;gas_emission_level=$lv[0];risk_color=$lv[0];color_hex=$lv[1];source_type='air_quality_proxy';geometry_mode=$geomMode;source_name=(''+$sn);source_url=Val $p @('source_url','url');source_date=$sd;last_source_update=$sd;source_confidence=$conf;confidence_percent=$conf;accuracy_scale=if($null -eq $conf){'UNKNOWN'}else{''+$conf+'/100'};confidence_level_label_tr=if($null -eq $conf){'Kaynak guveni belirtilmemis'}elseif($conf -ge 75){'Yuksek'}elseif($conf -ge 50){'Orta'}else{'Dusuk'};matching_method='existing parcel_air_quality_scores geometry proxy';evidence='Derived from existing local parcel_air_quality_scores.geojson feature; no official CO2e or greenhouse-gas source claimed.';calculation_explanation='emission_percent is mapped from pollutionRiskPercent as an air-quality pollution risk proxy. This is not official CO2e or greenhouse-gas emissions data. Point geometries are preserved as parcel-associated point proxies when parcel polygons are unavailable.';no_data_reason=$null}
  $features += @{type='Feature';geometry=$f.geometry;properties=$props}
  $rows += [pscustomobject]$props
  $ev += (@{parcel_id=$props.parcel_id;source_type='air_quality_proxy';geometry_mode=$props.geometry_mode;evidence=$props.evidence;calculation_explanation=$props.calculation_explanation}|ConvertTo-Json -Compress)
}
$outStatus=if($features.Count -gt 0){'PROXY_DATA_READY'}else{'NO_OUTPUT_FEATURES_AFTER_FILTER'}
$completion=if($features.Count -gt 0){70}else{60}
$next=if($features.Count -gt 0){'enqueue frontend binding patch and node check; if only point geometries are present, bind as point proxy layer or join to parcel polygons when available'}else{'inspect source geometry/properties and adjust contract without fake data'}
@{type='FeatureCollection';name='parcel_emissions_scores_air_quality_proxy';metadata=@{task_id=$Task;status=$outStatus;source_type='air_quality_proxy';geometry_support='Point,Polygon,MultiPolygon';fake_data=$false;db_write=$false;migration=$false;production_deploy=$false;input_feature_count=@($geo.features).Count;output_feature_count=$features.Count;point_feature_count=$pointCount;polygon_feature_count=$polygonCount;multi_polygon_feature_count=$multiPolygonCount;skipped=$skip};features=$features}|ConvertTo-Json -Depth 30|Set-Content -Encoding UTF8 $out
$rows|Export-Csv -NoTypeInformation -Encoding UTF8 $csv
@{task_id=$Task;status=if($features.Count -gt 0){'PROXY_DATA_READY_FRONTEND_PENDING'}else{'NO_OUTPUT_FEATURES_AFTER_FILTER'};source_type='air_quality_proxy';geometry_support='Point,Polygon,MultiPolygon';fake_data=$false;db_write=$false;migration=$false;production_deploy=$false;input_feature_count=@($geo.features).Count;output_feature_count=$features.Count;point_feature_count=$pointCount;polygon_feature_count=$polygonCount;multi_polygon_feature_count=$multiPolygonCount;frontend_patch_pending=($features.Count -gt 0)}|ConvertTo-Json -Depth 8|Set-Content -Encoding UTF8 $manifest
"source_type,source_name,calculation_explanation`nair_quality_proxy,AAYS parcel_air_quality_scores.geojson,pollutionRiskPercent mapped to emission_percent proxy; not official CO2e; point geometries preserved as point proxy when polygons unavailable"|Set-Content -Encoding UTF8 $registry
$ev|Set-Content -Encoding UTF8 $evidence
$result=@{task_id=$Task;status=if($features.Count -gt 0){'PROXY_DATA_READY_FRONTEND_PENDING'}else{'NO_OUTPUT_FEATURES_AFTER_FILTER'};completion_percent=$completion;generated_at=(Get-Date).ToString('s');final_ready=$false;fake_data=$false;db_write=$false;migration=$false;production_deploy=$false;source_type='air_quality_proxy';geometry_support='Point,Polygon,MultiPolygon';feature_count=$features.Count;input_feature_count=@($geo.features).Count;point_feature_count=$pointCount;polygon_feature_count=$polygonCount;multi_polygon_feature_count=$multiPolygonCount;skipped=$skip;outputs=@{geojson=$out;csv=$csv;manifest=$manifest;registry=$registry;evidence=$evidence};next_action=$next}
$result|ConvertTo-Json -Depth 10|Set-Content -Encoding UTF8 (Join-Path $GhReports ($Task+'.json'))
$result|ConvertTo-Json -Depth 10|Set-Content -Encoding UTF8 $Latest
@('task_id='+$Task,'status='+$result.status,'completion_percent='+$completion,'feature_count='+$features.Count,'point_feature_count='+$pointCount,'polygon_feature_count='+$polygonCount,'multi_polygon_feature_count='+$multiPolygonCount,'source_type=air_quality_proxy','fake_data=false','DB_WRITE=false','MIGRATION=false','PRODUCTION_DEPLOY=false','next_action='+$next)|Set-Content -Encoding UTF8 (Join-Path $GhReports ($Task+'.txt'))
git add england_map_web/data/parcel_emissions_scores.geojson england_map_web/data/parcel_emissions_scores.csv england_map_web/data/parcel_emissions_score_manifest.json england_map_web/data/parcel_emissions_source_registry.csv england_map_web/data/parcel_emissions_evidence_manifest.jsonl docs/chatgpt_status/reports docs/chatgpt_status/runner_outputs 2>$null
git commit -m 'gas-emissions: generate air-quality proxy parcel emissions data' 2>$null
git push origin $Branch
exit 0
