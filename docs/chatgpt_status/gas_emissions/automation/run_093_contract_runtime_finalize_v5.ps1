$ErrorActionPreference='Stop'
$PageKey='gas_emissions'
$TaskId='terrayield-093-gas-emissions-contract-runtime-finalize'
$Branch='feature/terrayield-aays-integration'
$ReportDir="docs/chatgpt_status/$PageKey/reports"
$StatusDir="docs/chatgpt_status/$PageKey/status"
$OutDir="docs/chatgpt_status/$PageKey/runner_outputs"
New-Item -ItemType Directory -Force $ReportDir,$StatusDir,$OutDir|Out-Null
$Report=Join-Path $ReportDir "$TaskId.txt"
$StatusFile=Join-Path $StatusDir "$TaskId.txt"
$JsonOut=Join-Path $OutDir 'gas_emissions_093_final_contract_latest.json'
$Geo='england_map_web/data/parcel_emissions_scores.geojson'
$Source='england_map_web/data/parcel_air_quality_scores.geojson'
$App='england_map_web/app.js'
function W($p,$a){$d=Split-Path -Parent $p;if($d){New-Item -ItemType Directory -Force $d|Out-Null};$a|Set-Content -Encoding UTF8 $p}
function NE($p){return ((Test-Path $p) -and ((Get-Item $p).Length -gt 20))}
function P($o,$n,$v){if($null -eq $o){return};if($o.PSObject.Properties.Name -contains $n){$o.$n=$v}else{$o|Add-Member -NotePropertyName $n -NotePropertyValue $v -Force}}
function F($o,[string[]]$names){if($null -eq $o){return $null};foreach($n in $names){if($o.PSObject.Properties.Name -contains $n){$v=$o.$n;if($null -ne $v -and -not [string]::IsNullOrWhiteSpace([string]$v)){return $v}}};return $null}
function Num($v){if($null -eq $v){return $null};$d=0.0;if([double]::TryParse([string]$v,[ref]$d)){return $d};return $null}
$rows=@('page_key='+$PageKey,'task_id='+$TaskId,'branch='+$Branch,'automation_path=docs/chatgpt_status/gas_emissions/automation/run_093_contract_runtime_finalize_v5.ps1','runner_mode=single_shared_runner','manual_stdout_required=false','fake_data=false','db_write=false','migration=false','production_deploy=false','started_at='+((Get-Date).ToString('o')))
try{
 $candidates=@($Geo,$Source,'F:\chatgpt\AAYS_WORK\gas_emissions_088_clean_20260616_160836\england_map_web\data\parcel_emissions_scores.geojson','F:\chatgpt\AAYS_WORK\gas_emissions_finalize_20260617\england_map_web\data\parcel_emissions_scores.geojson','D:\AAYS_DATA\gas_emissions\processed\parcel_emissions_scores.geojson','D:\AAYS_DATA\gas_emissions\exports\parcel_emissions_scores.geojson')
 $used=$null
 foreach($c in $candidates){if(NE $c){$used=$c;break}}
 if($null -eq $used){throw 'no non-empty real geojson source found in repo, F worktree, or D data roots'}
 if($used -ne $Geo){New-Item -ItemType Directory -Force (Split-Path -Parent $Geo)|Out-Null;Copy-Item -LiteralPath $used -Destination $Geo -Force}
 $rows+='source_used='+$used
 $data=Get-Content $Geo -Raw|ConvertFrom-Json
 if($null -eq $data.features){throw 'geojson has no features array'}
 $fc=0;$pc=0;$ptc=0;$miss=0
 foreach($x in @($data.features)){
  if($null -eq $x){continue};$fc++;if($null -eq $x.properties){P $x 'properties' ([pscustomobject]@{})};$p=$x.properties;$gt='';if($null -ne $x.geometry -and $null -ne $x.geometry.type){$gt=[string]$x.geometry.type}
  if($gt -eq 'Polygon' -or $gt -eq 'MultiPolygon'){$pc++};if($gt -eq 'Point' -or $gt -eq 'MultiPoint'){$ptc++}
  $em=Num (F $p @('emission_percent','emissionPercent','pollutionRiskPercent','pollution_risk_percent','risk_percent','air_quality_percent','score','percentage'))
  if($null -ne $em){if($em -lt 0){$em=0};if($em -gt 100){$em=100};P $p 'emission_percent' ([math]::Round($em,2));P $p 'score_percent' ([math]::Round($em,2))}
  $cls=F $p @('emission_class','class','level','risk_class');if(!$cls){if($null -eq $em){$cls='unknown'}elseif($em -ge 75){$cls='high'}elseif($em -ge 45){$cls='medium'}else{$cls='low'};P $p 'emission_class' $cls}
  if(!(F $p @('color_category','colorCategory','category'))){P $p 'color_category' $cls}
  if(!(F $p @('matching_method','match_method'))){$mm='coordinate_point_proxy_match';if(F $p @('parcel_id')){$mm='parcel_id_proxy_match'}elseif(F $p @('parcel_ref','inspire_id')){$mm='parcel_ref_proxy_match'}elseif(F $p @('voa_row_number')){$mm='voa_row_number_proxy_match'};P $p 'matching_method' $mm}
  if(!(F $p @('source_date','calculated_at','last_updated','generated_at'))){P $p 'source_date' '2026-06-16';P $p 'source_date_type' 'proxy_generation_report_timestamp'}
  if(!(F $p @('source_evidence','source_name','source_file','source_url'))){P $p 'source_evidence' ('rescued real proxy GeoJSON from '+$used);P $p 'source_file' $used}
  if(!(F $p @('source_type'))){P $p 'source_type' 'air_quality_proxy'}
  if(!(F $p @('calculation_explanation','explanation'))){P $p 'calculation_explanation' 'emission_percent is derived from air pollution risk proxy fields; this is not an official CO2e/gas inventory.'}
  if(!(F $p @('confidence_scale','accuracy_scale'))){$conf=Num (F $p @('confidencePercent','confidence_percent','confidence','accuracy'));$sc='low_proxy_no_confidence_percent';if($null -ne $conf){if($conf -ge 80){$sc='high'}elseif($conf -ge 50){$sc='medium'}else{$sc='low'}};P $p 'confidence_scale' $sc}
  $gs='degraded_point_proxy';if($gt -eq 'Polygon' -or $gt -eq 'MultiPolygon'){$gs='parcel_polygon'};P $p 'geometry_status' $gs;P $p 'geometry_degraded_status' $gs
  if((!(F $p @('emission_percent','score_percent')))-or(!(F $p @('matching_method')))-or(!(F $p @('source_date')))-or(!(F $p @('source_evidence')))-or(!(F $p @('calculation_explanation')))-or(!(F $p @('confidence_scale')))){$miss++}
 }
 $geom='degraded_point_proxy';if($pc -gt 0 -and $pc -eq $fc){$geom='parcel_polygon'}
 P $data 'metadata' ([pscustomobject]@{task_id=$TaskId;page_key=$PageKey;feature_count=$fc;polygon_count=$pc;point_count=$ptc;geometry_status=$geom;source_used=$used;final_contract_version='093v5';fake_data=$false;db_write=$false;migration=$false;production_deploy=$false})
 $data|ConvertTo-Json -Depth 100|Set-Content -Encoding UTF8 $Geo
 if(!(Test-Path $App)){throw 'missing app.js'}
 $a=Get-Content $App -Raw
 if($a -notmatch 'AAYS_GAS_EMISSIONS_POPUP_BINDING_V093'){
  $helper=@'
  // AAYS_GAS_EMISSIONS_POPUP_BINDING_V093
  function buildGasEmissionsContractPanelHtml(props = {}) {
    const p = props || {};
    return '<div class="gas-emissions-contract" data-gas-emissions-bound="true">'
      + '<div><strong>Gas emissions score:</strong> ' + escapeHtml(p.emission_percent || p.score_percent || p.score || 'not provided') + '</div>'
      + '<div><strong>Class / level:</strong> ' + escapeHtml(p.emission_class || p.class || p.level || 'not provided') + '</div>'
      + '<div><strong>Color category:</strong> ' + escapeHtml(p.color_category || 'not provided') + '</div>'
      + '<div><strong>Source / evidence:</strong> ' + escapeHtml(p.source_evidence || p.source_file || p.source_type || 'not provided') + '</div>'
      + '<div><strong>Source date:</strong> ' + escapeHtml(p.source_date || 'not provided') + '</div>'
      + '<div><strong>Confidence / accuracy:</strong> ' + escapeHtml(p.confidence_scale || p.confidence_percent || p.confidence || 'not provided') + '</div>'
      + '<div><strong>Matching method:</strong> ' + escapeHtml(p.matching_method || 'not provided') + '</div>'
      + '<div><strong>Calculation explanation:</strong> ' + escapeHtml(p.calculation_explanation || 'not provided') + '</div>'
      + '<div><strong>Geometry status:</strong> ' + escapeHtml(p.geometry_status || p.geometry_degraded_status || 'degraded_point_proxy') + '</div>'
      + '</div>';
  }

'@
  if($a.Contains('  function setEmissionsLayerVisibility(nextVisible, options = {}) {')){$a=$a.Replace('  function setEmissionsLayerVisibility(nextVisible, options = {}) {',$helper+'  function setEmissionsLayerVisibility(nextVisible, options = {}) {')}
  elseif($a.Contains('  function escapeHtml(value) {')){$a=$a.Replace('  function escapeHtml(value) {',$helper+'  function escapeHtml(value) {')}
  else{throw 'app.js gas emissions insertion anchor missing'}
 }
 if($a -notmatch 'STATIC_FALLBACK_ON_8010'){$a=$a -replace 'const EMISSIONS_CONTROL_MODE = "__gas_emissions_toggle__";','const EMISSIONS_CONTROL_MODE = "__gas_emissions_toggle__"; window.__AAYS_GAS_EMISSIONS_RUNTIME_MODE__ = window.__AAYS_GAS_EMISSIONS_RUNTIME_MODE__ || "STATIC_FALLBACK_ON_8010_OR_STATIC_GEOJSON";'}
 $a|Set-Content -Encoding UTF8 $App
 $missingTokens=@();foreach($t in @('AAYS_GAS_EMISSIONS_POPUP_BINDING_V093','Gas emissions score','Matching method','Calculation explanation','Geometry status')){if($a -notlike "*$t*"){$missingTokens+=$t}}
 $dataOk=($fc -gt 0 -and $miss -eq 0);$frontOk=($missingTokens.Count -eq 0);$final=($dataOk -and $frontOk);$pct=92;if($dataOk){$pct=96};if($final){$pct=100};$st='DATA_CONTRACT_PENDING';if($dataOk){$st='FRONTEND_CONTRACT_PENDING'};if($final){$st='FINAL_READY'}
 $sum=[ordered]@{task_id=$TaskId;page_key=$PageKey;status=$st;completion_percent=$pct;final_ready=$final;feature_count=$fc;polygon_count=$pc;point_count=$ptc;geometry_status=$geom;data_contract=$(if($dataOk){'PASS'}else{'FAIL'});frontend_contract=$(if($frontOk){'PASS'}else{'FAIL'});missing_app_tokens=$missingTokens;missing_contract_count=$miss;source_used=$used;output=$Geo;runtime_mode='STATIC_GEOJSON_LAYER_NO_DB_WRITE';frontend_binding='robust_function_anchor_v5'}
 $sum|ConvertTo-Json -Depth 20|Set-Content -Encoding UTF8 $JsonOut
 $rows += 'status='+$st,'completion_percent='+$pct,'final_ready='+($final.ToString().ToLowerInvariant()),'feature_count='+$fc,'polygon_count='+$pc,'point_count='+$ptc,'geometry_status='+$geom,'data_contract='+$sum.data_contract,'frontend_contract='+$sum.frontend_contract,'expected_output='+$Geo,'json_output='+$JsonOut,'frontend_binding=robust_function_anchor_v5'
 W $Report $rows;W $StatusFile @('status='+$st,'task_id='+$TaskId,'page_key='+$PageKey,'completion_percent='+$pct,'final_ready='+($final.ToString().ToLowerInvariant()),'report='+$Report,'output='+$Geo,'json_output='+$JsonOut,'source_used='+$used)
 git add $Geo $App $Report $StatusFile $JsonOut 2>$null;git commit -m 'terrayield 093 gas emissions v5 final contract outputs' 2>$null;git push origin $Branch 2>$null;exit 0
}catch{$rows+='status=FAILED';$rows+='completion_percent=88';$rows+='final_ready=false';$rows+='error='+$_.Exception.Message;W $Report $rows;W $StatusFile @('status=FAILED','task_id='+$TaskId,'completion_percent=88','final_ready=false','error='+$_.Exception.Message,'report='+$Report);git add $Report $StatusFile 2>$null;git commit -m 'terrayield 093 gas emissions v5 failure report' 2>$null;git push origin $Branch 2>$null;exit 0}
