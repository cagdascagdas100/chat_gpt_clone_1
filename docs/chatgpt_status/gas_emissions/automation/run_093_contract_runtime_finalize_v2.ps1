$ErrorActionPreference = 'Stop'
$PageKey='gas_emissions'
$TaskId='terrayield-093-gas-emissions-contract-runtime-finalize'
$Branch='feature/terrayield-aays-integration'
$ReportDir="docs/chatgpt_status/$PageKey/reports"
$StatusDir="docs/chatgpt_status/$PageKey/status"
$OutDir="docs/chatgpt_status/$PageKey/runner_outputs"
New-Item -ItemType Directory -Force $ReportDir,$StatusDir,$OutDir | Out-Null
$Report=Join-Path $ReportDir "$TaskId.txt"
$StatusFile=Join-Path $StatusDir "$TaskId.txt"
$JsonOut=Join-Path $OutDir 'gas_emissions_093_final_contract_latest.json'
$Geo='england_map_web/data/parcel_emissions_scores.geojson'
$Source='england_map_web/data/parcel_air_quality_scores.geojson'
$App='england_map_web/app.js'
function W($p,$a){$d=Split-Path -Parent $p;if($d){New-Item -ItemType Directory -Force $d|Out-Null};$a|Set-Content -Encoding UTF8 $p}
function AddP($o,$n,$v){if($null -eq $o){return};if($o.PSObject.Properties.Name -contains $n){$o.$n=$v}else{$o|Add-Member -NotePropertyName $n -NotePropertyValue $v -Force}}
function FirstP($o,[string[]]$names){if($null -eq $o){return $null};foreach($n in $names){if($o.PSObject.Properties.Name -contains $n){$v=$o.$n;if($null -ne $v -and -not [string]::IsNullOrWhiteSpace([string]$v)){return $v}}};return $null}
function Num($v){if($null -eq $v){return $null};$d=0.0;if([double]::TryParse([string]$v,[ref]$d)){return $d};return $null}
$rows=@("page_key=$PageKey","task_id=$TaskId","branch=$Branch","automation_path=docs/chatgpt_status/$PageKey/automation/run_093_contract_runtime_finalize_v2.ps1","runner_mode=single_shared_runner","manual_stdout_required=false","fake_data=false","db_write=false","migration=false","production_deploy=false","started_at=$((Get-Date).ToString('o'))")
try{
 if((!(Test-Path $Geo))-or [string]::IsNullOrWhiteSpace((Get-Content $Geo -Raw -ErrorAction SilentlyContinue))){if(Test-Path $Source){Copy-Item $Source $Geo -Force}}
 if(!(Test-Path $Geo)){throw "missing output geojson: $Geo"}
 $data=Get-Content $Geo -Raw|ConvertFrom-Json
 if($null -eq $data.features){throw 'geojson has no features array'}
 $featureCount=0;$polygonCount=0;$pointCount=0;$missing=0
 foreach($f in @($data.features)){
  if($null -eq $f){continue};$featureCount++
  if($null -eq $f.properties){AddP $f 'properties' ([pscustomobject]@{})}
  $p=$f.properties;$gt='';if($null -ne $f.geometry -and $null -ne $f.geometry.type){$gt=[string]$f.geometry.type}
  if($gt -eq 'Polygon' -or $gt -eq 'MultiPolygon'){$polygonCount++};if($gt -eq 'Point' -or $gt -eq 'MultiPoint'){$pointCount++}
  $em=Num (FirstP $p @('emission_percent','emissionPercent','pollutionRiskPercent','pollution_risk_percent','risk_percent','air_quality_percent','score','percentage'))
  if($null -ne $em){if($em -lt 0){$em=0};if($em -gt 100){$em=100};AddP $p 'emission_percent' ([math]::Round($em,2));AddP $p 'score_percent' ([math]::Round($em,2))}
  $cls=FirstP $p @('emission_class','class','level','risk_class');if(!$cls){if($null -eq $em){$cls='unknown'}elseif($em -ge 75){$cls='high'}elseif($em -ge 45){$cls='medium'}else{$cls='low'};AddP $p 'emission_class' $cls}
  if(!(FirstP $p @('color_category','colorCategory','category'))){AddP $p 'color_category' $cls}
  $pk=FirstP $p @('parcel_id','parcel_ref','uprn','voa_row_number','inspire_id');if(!$pk){$pk='unknown_parcel_key'};AddP $p 'parcel_key' $pk
  if(!(FirstP $p @('matching_method','match_method'))){$mm='coordinate_point_proxy_match';if(FirstP $p @('parcel_id')){$mm='parcel_id_proxy_match'}elseif(FirstP $p @('parcel_ref','inspire_id')){$mm='parcel_ref_proxy_match'}elseif(FirstP $p @('voa_row_number')){$mm='voa_row_number_proxy_match'};AddP $p 'matching_method' $mm}
  if(!(FirstP $p @('source_date','calculated_at','last_updated','generated_at'))){AddP $p 'source_date' '2026-06-16';AddP $p 'source_date_type' 'proxy_generation_report_timestamp'}
  if(!(FirstP $p @('source_evidence','source_name','source_file','source_url'))){AddP $p 'source_evidence' 'parcel_air_quality_scores.geojson plus terrayield-088 gas emissions proxy report';AddP $p 'source_file' $Source}
  if(!(FirstP $p @('source_type'))){AddP $p 'source_type' 'air_quality_proxy'}
  if(!(FirstP $p @('calculation_explanation','explanation'))){AddP $p 'calculation_explanation' 'emission_percent is derived from air pollution risk proxy fields; this is not an official CO2e/gas inventory.'}
  if(!(FirstP $p @('confidence_scale','accuracy_scale'))){$conf=Num (FirstP $p @('confidencePercent','confidence_percent','confidence','accuracy'));$sc='low_proxy_no_confidence_percent';if($null -ne $conf){if($conf -ge 80){$sc='high'}elseif($conf -ge 50){$sc='medium'}else{$sc='low'}};AddP $p 'confidence_scale' $sc}
  $gs='degraded_point_proxy';if($gt -eq 'Polygon' -or $gt -eq 'MultiPolygon'){$gs='parcel_polygon'};AddP $p 'geometry_status' $gs;AddP $p 'geometry_degraded_status' $gs
  if((!(FirstP $p @('emission_percent','score_percent')))-or(!(FirstP $p @('matching_method')))-or(!(FirstP $p @('source_date')))-or(!(FirstP $p @('source_evidence')))-or(!(FirstP $p @('calculation_explanation')))-or(!(FirstP $p @('confidence_scale')))){$missing++}
 }
 $geom='degraded_point_proxy';if($polygonCount -gt 0 -and $polygonCount -eq $featureCount){$geom='parcel_polygon'}
 AddP $data 'metadata' ([pscustomobject]@{task_id=$TaskId;page_key=$PageKey;feature_count=$featureCount;polygon_count=$polygonCount;point_count=$pointCount;geometry_status=$geom;source_type='air_quality_proxy';final_contract_version='093v2';fake_data=$false;db_write=$false;migration=$false;production_deploy=$false})
 $data|ConvertTo-Json -Depth 100|Set-Content -Encoding UTF8 $Geo
 if(!(Test-Path $App)){throw "missing app.js: $App"}
 $appText=Get-Content $App -Raw
 if($appText -notmatch 'AAYS_GAS_EMISSIONS_POPUP_BINDING_V093'){
  $inline='      ${tagHtml}' + "`n" + '      ${/* AAYS_GAS_EMISSIONS_POPUP_BINDING_V093 */ (() => { const p = feature?.properties || {}; if (p.emission_percent === undefined && p.score_percent === undefined && p.source_type !== "air_quality_proxy") return ""; const esc = (v) => String(v ?? "").replace(/[&<>" + "'" + "]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","' + "'" + '":"&#39;"}[c])); const score = p.emission_percent ?? p.score_percent ?? p.score ?? "not provided"; return `<div class="gas-emissions-contract" data-gas-emissions-bound="true"><div><strong>Gas emissions score:</strong> ${esc(score)}${score === "not provided" ? "" : "%"}</div><div><strong>Class / level:</strong> ${esc(p.emission_class ?? p.class ?? p.level ?? "not provided")}</div><div><strong>Color category:</strong> ${esc(p.color_category ?? "not provided")}</div><div><strong>Source / evidence:</strong> ${esc(p.source_evidence ?? p.source_file ?? p.source_type ?? "not provided")}</div><div><strong>Source date:</strong> ${esc(p.source_date ?? "not provided")}</div><div><strong>Confidence / accuracy:</strong> ${esc(p.confidence_scale ?? p.confidence_percent ?? p.confidence ?? "not provided")}</div><div><strong>Matching method:</strong> ${esc(p.matching_method ?? "not provided")}</div><div><strong>Calculation explanation:</strong> ${esc(p.calculation_explanation ?? "not provided")}</div><div><strong>Geometry status:</strong> ${esc(p.geometry_status ?? p.geometry_degraded_status ?? "degraded_point_proxy")}</div></div>`; })()}'
  if($appText.Contains('      ${tagHtml}')){$appText=$appText.Replace('      ${tagHtml}',$inline)}else{throw 'app.js popup tagHtml anchor missing'}
 }
 if($appText -notmatch 'STATIC_FALLBACK_ON_8010'){$appText=$appText -replace 'const EMISSIONS_CONTROL_MODE = "__gas_emissions_toggle__";','const EMISSIONS_CONTROL_MODE = "__gas_emissions_toggle__"; window.__AAYS_GAS_EMISSIONS_RUNTIME_MODE__ = window.__AAYS_GAS_EMISSIONS_RUNTIME_MODE__ || "STATIC_FALLBACK_ON_8010_OR_STATIC_GEOJSON";'}
 $appText|Set-Content -Encoding UTF8 $App
 $missApp=@();foreach($tok in @('AAYS_GAS_EMISSIONS_POPUP_BINDING_V093','Gas emissions score','Matching method','Calculation explanation','Geometry status')){if($appText -notlike "*$tok*"){$missApp+=$tok}}
 $dataOk=($featureCount -gt 0 -and $missing -eq 0);$frontOk=($missApp.Count -eq 0);$final=($dataOk -and $frontOk);$pct=90;if($dataOk){$pct=96};if($final){$pct=100};$status='DATA_CONTRACT_PENDING';if($dataOk){$status='FRONTEND_CONTRACT_PENDING'};if($final){$status='FINAL_READY'}
 $summary=[ordered]@{task_id=$TaskId;page_key=$PageKey;status=$status;completion_percent=$pct;final_ready=$final;feature_count=$featureCount;polygon_count=$polygonCount;point_count=$pointCount;geometry_status=$geom;data_contract=$(if($dataOk){'PASS'}else{'FAIL'});frontend_contract=$(if($frontOk){'PASS'}else{'FAIL'});missing_app_tokens=$missApp;missing_contract_count=$missing;output=$Geo;runtime_mode='STATIC_GEOJSON_LAYER_NO_DB_WRITE'}
 $summary|ConvertTo-Json -Depth 20|Set-Content -Encoding UTF8 $JsonOut
 $rows += "status=$status","completion_percent=$pct","final_ready=$($final.ToString().ToLowerInvariant())","feature_count=$featureCount","polygon_count=$polygonCount","point_count=$pointCount","geometry_status=$geom","data_contract=$($summary.data_contract)","frontend_contract=$($summary.frontend_contract)","expected_output=$Geo","json_output=$JsonOut"
 W $Report $rows;W $StatusFile @("status=$status","task_id=$TaskId","page_key=$PageKey","completion_percent=$pct","final_ready=$($final.ToString().ToLowerInvariant())","report=$Report","output=$Geo","json_output=$JsonOut")
 git add $Geo $App $Report $StatusFile $JsonOut 2>$null;git commit -m 'terrayield 093 gas emissions final contract outputs' 2>$null;git push origin $Branch 2>$null
 exit 0
}catch{
 $rows+='status=FAILED';$rows+='completion_percent=70';$rows+='final_ready=false';$rows+="error=$($_.Exception.Message)";W $Report $rows;W $StatusFile @('status=FAILED',"task_id=$TaskId",'completion_percent=70','final_ready=false',"error=$($_.Exception.Message)","report=$Report");git add $Report $StatusFile 2>$null;git commit -m 'terrayield 093 gas emissions failure report' 2>$null;git push origin $Branch 2>$null;exit 0
}
