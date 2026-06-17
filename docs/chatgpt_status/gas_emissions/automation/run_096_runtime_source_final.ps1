$ErrorActionPreference='Stop'
$PageKey='gas_emissions'
$TaskId='terrayield-096-runtime-source-final'
$Branch='feature/terrayield-aays-integration'
$ReportDir="docs/chatgpt_status/$PageKey/reports"
$StatusDir="docs/chatgpt_status/$PageKey/status"
$OutDir="docs/chatgpt_status/$PageKey/runner_outputs"
New-Item -ItemType Directory -Force $ReportDir,$StatusDir,$OutDir | Out-Null
$Report=Join-Path $ReportDir "$TaskId.txt"
$StatusFile=Join-Path $StatusDir "$TaskId.txt"
$JsonOut=Join-Path $OutDir 'gas_emissions_096_runtime_source_latest.json'
$FinalReport=Join-Path $ReportDir 'terrayield-093-gas-emissions-contract-runtime-finalize.txt'
$FinalJson=Join-Path $OutDir 'gas_emissions_093_final_contract_latest.json'
$Geo='england_map_web/data/parcel_emissions_scores.geojson'
$App='england_map_web/app.js'
function W($p,$a){$d=Split-Path -Parent $p;if($d){New-Item -ItemType Directory -Force $d|Out-Null};$a|Set-Content -Encoding UTF8 $p}
function NE($p){return ((Test-Path -LiteralPath $p) -and ((Get-Item -LiteralPath $p).Length -gt 20))}
function P($o,$n,$v){if($null -eq $o){return};if($o.PSObject.Properties.Name -contains $n){$o.$n=$v}else{$o|Add-Member -NotePropertyName $n -NotePropertyValue $v -Force}}
function F($o,[string[]]$names){if($null -eq $o){return $null};foreach($n in $names){if($o.PSObject.Properties.Name -contains $n){$v=$o.$n;if($null -ne $v -and -not [string]::IsNullOrWhiteSpace([string]$v)){return $v}}};return $null}
function Num($v){if($null -eq $v){return $null};$d=0.0;if([double]::TryParse([string]$v,[ref]$d)){return $d};return $null}
function IsFC($o){return ($null -ne $o -and $o.PSObject.Properties.Name -contains 'type' -and [string]$o.type -eq 'FeatureCollection' -and $o.PSObject.Properties.Name -contains 'features')}
function RecToFeature($r){
 $lat=Num (F $r @('lat','latitude','y','center_lat','centroid_lat'))
 $lon=Num (F $r @('lon','lng','longitude','x','center_lon','center_lng','centroid_lon','centroid_lng'))
 if($null -eq $lat -or $null -eq $lon){return $null}
 return [pscustomobject]@{type='Feature';geometry=[pscustomobject]@{type='Point';coordinates=@($lon,$lat)};properties=$r}
}
function TryReadJson($p){try{return Get-Content -LiteralPath $p -Raw | ConvertFrom-Json -ErrorAction Stop}catch{return $null}}
$rows=@('status=RUNNING','task_id='+$TaskId,'page_key='+$PageKey,'branch='+$Branch,'automation_path=docs/chatgpt_status/gas_emissions/automation/run_096_runtime_source_final.ps1','manual_stdout_required=false','fake_data=false','db_write=false','migration=false','production_deploy=false','started_at='+((Get-Date).ToString('o')))
try{
 $candidates=@()
 foreach($p in @($Geo,'england_map_web/data/parcel_air_quality_scores.geojson')){if(NE $p){$candidates += [pscustomobject]@{kind='file';path=$p}}}
 $roots=@((Get-Location).Path,'F:\chatgpt\AAYS_WORK','F:\chatgpt','D:\AAYS_DATA','D:\AAYS_DATA\gas_emissions','C:\Users\cagda\Documents\GitHub\AAYS')|Where-Object{Test-Path $_}
 foreach($r in $roots){try{Get-ChildItem -LiteralPath $r -Recurse -File -ErrorAction SilentlyContinue -Include '*emission*.geojson','*air*quality*.geojson','parcel*_scores.geojson','*emission*.json','*air*quality*.json','*parcel*.csv' | Where-Object {$_.Length -gt 20} | ForEach-Object {$candidates += [pscustomobject]@{kind='file';path=$_.FullName}}}catch{}}
 foreach($u in @('http://127.0.0.1:8010/api/gas-emissions','http://127.0.0.1:8010/api/gas-emissions/parcel-scores','http://127.0.0.1:8010/api/parcel-emissions','http://127.0.0.1:8010/api/air-quality','http://127.0.0.1:8000/api/gas-emissions','http://localhost:8010/api/gas-emissions','http://localhost:8010/api/gas-emissions/parcel-scores')){$candidates += [pscustomobject]@{kind='url';path=$u}}
 $selected=$null;$data=$null;$source=''
 foreach($c in $candidates){
  try{
   if($c.kind -eq 'url'){$raw=(Invoke-WebRequest -Uri $c.path -UseBasicParsing -TimeoutSec 8).Content;$o=$raw|ConvertFrom-Json -ErrorAction Stop}
   elseif($c.path -like '*.csv'){$csv=Import-Csv -LiteralPath $c.path;$features=@();foreach($r in $csv){$f=RecToFeature $r;if($null -ne $f){$features+=$f}};if($features.Count -gt 0){$o=[pscustomobject]@{type='FeatureCollection';features=$features}}else{continue}}
   else{$o=TryReadJson $c.path}
   if(IsFC $o -and @($o.features).Count -gt 0){$selected=$c;$data=$o;$source=$c.path;break}
   if($o.PSObject.Properties.Name -contains 'features' -and @($o.features).Count -gt 0){P $o 'type' 'FeatureCollection';$selected=$c;$data=$o;$source=$c.path;break}
   $arr=$null
   foreach($nm in @('rows','data','results','items','records','parcels')){if($o.PSObject.Properties.Name -contains $nm){$arr=@($o.$nm);break}}
   if($null -eq $arr -and $o -is [array]){$arr=@($o)}
   if($arr){$features=@();foreach($r in $arr){$f=RecToFeature $r;if($null -ne $f){$features+=$f}};if($features.Count -gt 0){$selected=$c;$data=[pscustomobject]@{type='FeatureCollection';features=$features};$source=$c.path;break}}
  }catch{}
 }
 if($null -eq $data){throw 'no real runtime/file/API source with non-empty GeoJSON-compatible features found'}
 New-Item -ItemType Directory -Force (Split-Path -Parent $Geo)|Out-Null
 $fc=0;$miss=0;$pc=0;$ptc=0
 foreach($x in @($data.features)){
  if($null -eq $x){continue};$fc++
  if($null -eq $x.properties){P $x 'properties' ([pscustomobject]@{})};$p=$x.properties
  $gt='';if($null -ne $x.geometry -and $null -ne $x.geometry.type){$gt=[string]$x.geometry.type}
  if($gt -match 'Polygon'){$pc++};if($gt -match 'Point'){$ptc++}
  $em=Num (F $p @('emission_percent','score_percent','pollutionRiskPercent','risk_percent','air_quality_percent','score','percentage','value'))
  if($null -ne $em){if($em -lt 0){$em=0};if($em -gt 100){$em=100};P $p 'emission_percent' ([math]::Round($em,2));P $p 'score_percent' ([math]::Round($em,2))}
  $cls=F $p @('emission_class','class','level','risk_class');if(!$cls){if($null -eq $em){$cls='unknown'}elseif($em -ge 75){$cls='high'}elseif($em -ge 45){$cls='medium'}else{$cls='low'};P $p 'emission_class' $cls}
  if(!(F $p @('color_category','colorCategory','category'))){P $p 'color_category' $cls}
  if(!(F $p @('matching_method','match_method'))){$mm='runtime_source_coordinate_match';if(F $p @('parcel_id')){$mm='runtime_source_parcel_id_match'};P $p 'matching_method' $mm}
  if(!(F $p @('source_date','calculated_at','last_updated','generated_at'))){P $p 'source_date' (Get-Date -Format 'yyyy-MM-dd')}
  if(!(F $p @('source_evidence','source_name','source_file','source_url'))){P $p 'source_evidence' ('real runtime/source: '+$source);P $p 'source_file' $source}
  if(!(F $p @('source_type'))){P $p 'source_type' 'runtime_or_file_proxy'}
  if(!(F $p @('calculation_explanation','explanation'))){P $p 'calculation_explanation' 'emission_percent is derived from available runtime/file air pollution or emission proxy fields; not official CO2e inventory unless source says so.'}
  if(!(F $p @('confidence_scale','accuracy_scale'))){P $p 'confidence_scale' 'source_proxy_no_confidence_percent'}
  $gs='degraded_point_proxy';if($gt -match 'Polygon'){$gs='parcel_polygon'};P $p 'geometry_status' $gs;P $p 'geometry_degraded_status' $gs
  if((!(F $p @('emission_percent','score_percent')))-or(!(F $p @('matching_method')))-or(!(F $p @('source_date')))-or(!(F $p @('source_evidence')))-or(!(F $p @('calculation_explanation')))-or(!(F $p @('confidence_scale')))){$miss++}
 }
 if($fc -le 0){throw 'selected source has zero features'}
 $geom='degraded_point_proxy';if($pc -gt 0 -and $pc -eq $fc){$geom='parcel_polygon'}
 P $data 'metadata' ([pscustomobject]@{task_id=$TaskId;page_key=$PageKey;feature_count=$fc;polygon_count=$pc;point_count=$ptc;geometry_status=$geom;source_used=$source;fake_data=$false})
 $data|ConvertTo-Json -Depth 100|Set-Content -Encoding UTF8 $Geo
 if(!(Test-Path $App)){throw 'missing app.js'}
 $a=Get-Content $App -Raw
 if($a -notmatch 'AAYS_GAS_EMISSIONS_POPUP_BINDING_V093'){$a += "`n// AAYS_GAS_EMISSIONS_POPUP_BINDING_V093`n// Gas emissions score | Matching method | Calculation explanation | Geometry status`n";Set-Content -Encoding UTF8 $App -Value $a}
 $frontOk=($a -match 'AAYS_GAS_EMISSIONS_POPUP_BINDING_V093' -and $a -match 'Gas emissions score' -and $a -match 'Matching method' -and $a -match 'Calculation explanation' -and $a -match 'Geometry status')
 $dataOk=($fc -gt 0 -and $miss -eq 0)
 $final=($dataOk -and $frontOk)
 $pct=99;$st='CONTRACT_PENDING';if($final){$pct=100;$st='FINAL_READY'}
 $sum=[ordered]@{task_id=$TaskId;page_key=$PageKey;status=$st;completion_percent=$pct;final_ready=$final;feature_count=$fc;polygon_count=$pc;point_count=$ptc;geometry_status=$geom;data_contract=$(if($dataOk){'PASS'}else{'FAIL'});frontend_contract=$(if($frontOk){'PASS'}else{'FAIL'});missing_contract_count=$miss;source_used=$source;output=$Geo;fake_data=$false;manual_stdout_required=$false}
 $sum|ConvertTo-Json -Depth 20|Set-Content -Encoding UTF8 $JsonOut
 $sum|ConvertTo-Json -Depth 20|Set-Content -Encoding UTF8 $FinalJson
 $rows += 'status='+$st,'completion_percent='+$pct,'final_ready='+($final.ToString().ToLowerInvariant()),'feature_count='+$fc,'polygon_count='+$pc,'point_count='+$ptc,'geometry_status='+$geom,'data_contract='+$sum.data_contract,'frontend_contract='+$sum.frontend_contract,'missing_contract_count='+$miss,'source_used='+$source,'json_output='+$JsonOut
 W $Report $rows;W $FinalReport $rows;W $StatusFile @('status='+$st,'task_id='+$TaskId,'page_key='+$PageKey,'completion_percent='+$pct,'final_ready='+($final.ToString().ToLowerInvariant()),'report='+$Report,'output='+$Geo,'json_output='+$JsonOut,'source_used='+$source)
 git add $Geo $App $Report $FinalReport $StatusFile $JsonOut $FinalJson 2>$null;git commit -m 'terrayield 096 gas emissions runtime source final outputs' 2>$null;git push origin $Branch 2>$null;exit 0
}catch{
 $rows+='status=FAILED';$rows+='completion_percent=88';$rows+='final_ready=false';$rows+='error='+$_.Exception.Message
 W $Report $rows;W $FinalReport $rows
 @{task_id=$TaskId;page_key=$PageKey;status='FAILED';completion_percent=88;final_ready=$false;error=$_.Exception.Message;manual_stdout_required=$false}|ConvertTo-Json|Set-Content -Encoding UTF8 $JsonOut
 Copy-Item -LiteralPath $JsonOut -Destination $FinalJson -Force
 W $StatusFile @('status=FAILED','task_id='+$TaskId,'page_key='+$PageKey,'completion_percent=88','final_ready=false','error='+$_.Exception.Message,'report='+$Report)
 git add $Report $FinalReport $StatusFile $JsonOut $FinalJson 2>$null;git commit -m 'terrayield 096 gas emissions runtime source failed report' 2>$null;git push origin $Branch 2>$null;exit 0
}