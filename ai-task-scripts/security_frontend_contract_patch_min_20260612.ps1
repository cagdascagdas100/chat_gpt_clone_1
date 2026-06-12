$ErrorActionPreference='Continue'
$Bridge='C:\AAYS_GITHUB_BRIDGE_CLEAN2'
$Repo='C:\Users\cagda\Documents\GitHub\AAYS'
$Page='security_public_safety_low_credit_20260612'
$Stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$OutDir=Join-Path $Bridge "docs\chatgpt_status\$Page\runner_output"
$StatusDir=Join-Path $Bridge "docs\chatgpt_status\$Page\status"
$ReportDir=Join-Path $Bridge "docs\chatgpt_status\$Page\reports"
$HbDir=Join-Path $Bridge "docs\chatgpt_status\$Page\heartbeat"
$AiDir=Join-Path $Bridge 'ai-results'
foreach($d in @($OutDir,$StatusDir,$ReportDir,$HbDir,$AiDir)){New-Item -ItemType Directory -Force -Path $d|Out-Null}
$Log=Join-Path $OutDir "security_frontend_contract_patch_min_$Stamp.txt"
function L($m){$m|Tee-Object -FilePath $Log -Append}
function W($p,$t){New-Item -ItemType Directory -Force -Path (Split-Path -Parent $p)|Out-Null;[IO.File]::WriteAllText($p,$t,[Text.UTF8Encoding]::new($false))}
L "TASK=security-public-safety-frontend-contract-patch-min-20260612"
L "Repo=$Repo"
if(!(Test-Path $Repo)){L 'FAIL=APP_ROOT_MISSING';exit 2}
$Web=Join-Path $Repo 'england_map_web'
$JsPath=Join-Path $Web 'security_overlay.js'
$CssPath=Join-Path $Web 'security_overlay.css'
$DataPath=Join-Path $Web 'data\parcel_security_scores_rechecked_0_120m_spatial.geojson'
$SummaryPath=Join-Path $Web 'data\parcel_security_match_summary.json'
if(Test-Path $JsPath){Copy-Item $JsPath "$JsPath.bak_$Stamp" -Force}
if(Test-Path $CssPath){Copy-Item $CssPath "$CssPath.bak_$Stamp" -Force}
$Js=@'
/* AAYS_SECURITY_CONTRACT_PATCH_20260612 */
(function(){
'use strict';
const DATA_URL='./data/parcel_security_scores_rechecked_0_120m_spatial.geojson';
const SUMMARY_URL='./data/parcel_security_match_summary.json';
const SRC='aays-security-source', FILL='aays-security-fill', LINE='aays-security-line', POINT='aays-security-points';
const MISS='MISSING_IN_CURRENT_DATA_CONTRACT';
const LV=[['very_low','Very Low / Cok Dusuk','#7f1d1d'],['low','Low / Dusuk','#ef4444'],['medium','Medium / Orta','#f59e0b'],['good','Good / Iyi','#22c55e'],['very_good','Very Good / Cok Iyi','#065f46']];
const SCORE=['to-number',['coalesce',['get','security_score'],['get','safety_score'],-1],-1];
const COLOR=['case',['!=',['coalesce',['get','security_color_hex'],''],''],['get','security_color_hex'],['>=',SCORE,81],'#065f46',['>=',SCORE,61],'#22c55e',['>=',SCORE,41],'#f59e0b',['>=',SCORE,21],'#ef4444',['>=',SCORE,0],'#7f1d1d',['match',['get','safety_level'],'Cok Dusuk','#7f1d1d','Cok Düşük','#7f1d1d','Dusuk','#ef4444','Düşük','#ef4444','Orta','#f59e0b','Iyi','#22c55e','İyi','#22c55e','Cok Iyi','#065f46','Çok İyi','#065f46','#6b7280']];
let map=null,visible=false,loaded=false,pop=null,summary=null;
function findMap(){return window.map||window.aaysMap||window.__AAYS_MAP__||window.terrayieldMap||null}
function esc(v){return String(v==null||v===''?'-':v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function first(p,a,fb){for(const k of a){if(p[k]!==undefined&&p[k]!==null&&p[k]!=='')return p[k]}return fb}
function num(v){const n=Number(v);return Number.isFinite(n)?n:null}
function cls(p){const s=num(first(p,['security_score','safety_score'],null)); if(s!==null){if(s>=81)return LV[4];if(s>=61)return LV[3];if(s>=41)return LV[2];if(s>=21)return LV[1];if(s>=0)return LV[0];} const r=String(first(p,['security_level','safety_level','security_level_label'],'')).toLowerCase(); if(r.includes('cok')&&r.includes('iyi'))return LV[4]; if(r.includes('iyi'))return LV[3]; if(r.includes('orta'))return LV[2]; if(r.includes('dusuk')||r.includes('düşük'))return (r.includes('cok')||r.includes('çok'))?LV[0]:LV[1]; return ['no_data','No data / Veri yok','#6b7280'];}
function acc(p){const c=num(p.confidence_score); if(c===null)return first(p,['accuracy_rating','confidence_label'],MISS); if(c>=90)return 'Very High Accuracy'; if(c>=75)return 'High Accuracy'; if(c>=50)return 'Medium Accuracy'; return 'Low Accuracy';}
function row(k,v){return '<div class="aays-security-popup-row"><b>'+esc(k)+':</b> <span>'+esc(v)+'</span></div>'}
function rows(p){const c=cls(p), no=first(p,['no_data_reason'], first(p,['security_match_status'],'')==='MATCHED'?'':'Unmatched or no polygon-level evidence in current feature'); return [['parcel_id',first(p,['parcel_id','id'],MISS)],['security_parcel_id',first(p,['security_parcel_id'],MISS)],['layer_name',first(p,['layer_name'],'Safety / Security')],['security_score',first(p,['security_score','safety_score'],MISS)],['security_level',first(p,['security_level','safety_level'],c[1])],['security_level_label',first(p,['security_level_label'],c[1])],['security_color_category',first(p,['security_color_category'],c[0])],['security_color_hex',first(p,['security_color_hex'],c[2])],['crime_rate / weighted_crime_12m',first(p,['crime_rate','weighted_crime_12m'],MISS)],['police_safety_level',first(p,['police_safety_level'],MISS)],['nearest_police_station_distance_m',first(p,['nearest_police_station_distance_m'],MISS)],['incident_density',first(p,['incident_density'],MISS)],['source_name',first(p,['source_name'],MISS)],['source_url / local_source_path',first(p,['source_url','local_source_path'],DATA_URL)],['source_date',first(p,['source_date','crime_data_date'],MISS)],['evidence',first(p,['evidence','source_evidence','evidence_summary'],MISS)],['matching_method',first(p,['matching_method','spatial_match_method'],MISS)],['calculation_explanation',first(p,['calculation_explanation','score_explanation'],MISS)],['confidence_score',first(p,['confidence_score'],MISS)],['accuracy_rating',acc(p)],['confidence_flags',first(p,['confidence_flags'],'')],['no_data_reason',no]];}
function ui(){if(document.getElementById('aays-security-root'))return; const r=document.createElement('div'); r.id='aays-security-root'; r.innerHTML='<button id="aays-security-toggle" type="button">Güvenlik</button><div id="aays-security-panel"><div class="aays-security-title">Safety / Security Parcel Layer</div><div class="aays-security-sub">5 seviyeli sınıflama; eksik kaynak/tarih/evidence sahte doldurulmaz.</div><div class="aays-security-legend"><span style="background:#7f1d1d"></span>0-20 Very Low</div><div class="aays-security-legend"><span style="background:#ef4444"></span>21-40 Low</div><div class="aays-security-legend"><span style="background:#f59e0b"></span>41-60 Medium</div><div class="aays-security-legend"><span style="background:#22c55e"></span>61-80 Good</div><div class="aays-security-legend"><span style="background:#065f46"></span>81-100 Very Good</div><div class="aays-security-legend"><span style="background:#6b7280"></span>No data</div><div id="aays-security-stat">Veri bekleniyor...</div><div class="aays-security-note">Anonim/aggregate kamu verisi kesin parsel olay noktası olarak sunulmaz.</div></div>'; document.body.appendChild(r); document.getElementById('aays-security-toggle').addEventListener('click',toggle); fetch(SUMMARY_URL).then(x=>x.ok?x.json():null).then(s=>{summary=s;stat()}).catch(stat);}
function stat(){const e=document.getElementById('aays-security-stat'); if(!e)return; e.textContent=summary?`Summary: total=${summary.total_parcels||'-'} matched=${summary.matched_parcels||'-'} unmatched=${summary.unmatched_parcels||'-'}`:(loaded?'Layer yüklendi; summary okunamadı.':'Veri bekleniyor...');}
function setVis(v){[FILL,LINE,POINT].forEach(id=>{try{if(map&&map.getLayer(id))map.setLayoutProperty(id,'visibility',v)}catch(_){}})}
function bind(id){if(!map||!map.getLayer(id)||map['__aays_'+id])return; map['__aays_'+id]=1; map.on('click',id,e=>{const f=e.features&&e.features[0]; if(!f)return; const html='<div class="aays-security-popup"><div class="aays-security-popup-title">Concrete Output</div>'+rows(f.properties||{}).map(x=>row(x[0],x[1])).join('')+'<div class="aays-security-popup-note">Final kabul için polygon renklendirme veya parcel-source join doğrulanmalıdır.</div></div>'; const P=(window.maplibregl||window.mapboxgl||{}).Popup; if(!P)return; if(pop)pop.remove(); pop=new P({closeButton:true,closeOnClick:true,maxWidth:'460px'}).setLngLat(e.lngLat).setHTML(html).addTo(map);}); map.on('mouseenter',id,()=>{try{map.getCanvas().style.cursor='pointer'}catch(_){}}); map.on('mouseleave',id,()=>{try{map.getCanvas().style.cursor=''}catch(_){}});}
function layers(){if(!map||!map.isStyleLoaded||!map.isStyleLoaded()){setTimeout(layers,350);return} if(!map.getSource(SRC))map.addSource(SRC,{type:'geojson',data:DATA_URL,promoteId:'security_parcel_id'}); if(!map.getLayer(FILL))map.addLayer({id:FILL,type:'fill',source:SRC,filter:['any',['==',['geometry-type'],'Polygon'],['==',['geometry-type'],'MultiPolygon']],paint:{'fill-color':COLOR,'fill-opacity':['case',['==',['get','security_match_status'],'MATCHED'],.52,.18]},layout:{visibility:'none'}}); if(!map.getLayer(LINE))map.addLayer({id:LINE,type:'line',source:SRC,filter:['any',['==',['geometry-type'],'Polygon'],['==',['geometry-type'],'MultiPolygon']],paint:{'line-color':'#111827','line-width':.9,'line-opacity':.55},layout:{visibility:'none'}}); if(!map.getLayer(POINT))map.addLayer({id:POINT,type:'circle',source:SRC,filter:['==',['geometry-type'],'Point'],paint:{'circle-color':COLOR,'circle-radius':['interpolate',['linear'],['zoom'],5,2,9,3.5,13,5.5,16,7],'circle-opacity':['case',['==',['get','security_match_status'],'MATCHED'],.82,.28],'circle-stroke-color':'#111827','circle-stroke-width':.65},layout:{visibility:'none'}}); bind(FILL);bind(POINT);loaded=true;stat(); if(visible)setVis('visible');}
function activate(){ui(); map=map||findMap(); if(!map){setTimeout(activate,450);return} visible=true; document.getElementById('aays-security-root')?.classList.add('open'); document.getElementById('aays-security-toggle')?.classList.add('active'); layers(); setVis('visible');}
function deactivate(){visible=false; document.getElementById('aays-security-root')?.classList.remove('open'); document.getElementById('aays-security-toggle')?.classList.remove('active'); setVis('none'); if(pop)pop.remove();}
function toggle(){visible?deactivate():activate()}
window.AAYS_SECURITY={activate,deactivate,toggle,addLayers:function(){map=map||findMap(); if(map)layers();}};
document.addEventListener('DOMContentLoaded',ui);
})();
'@
$Css=@'
/* AAYS_SECURITY_CONTRACT_PATCH_20260612 */
#aays-security-root{position:absolute;right:18px;top:82px;z-index:25;font-family:Inter,Arial,sans-serif}#aays-security-toggle{border:0;border-radius:12px;padding:9px 12px;background:#111827;color:#fff;font-weight:700;box-shadow:0 8px 24px rgba(0,0,0,.18)}#aays-security-toggle.active{background:#065f46}#aays-security-panel{display:none;margin-top:8px;width:282px;background:rgba(255,255,255,.96);border:1px solid rgba(17,24,39,.14);border-radius:14px;padding:12px;box-shadow:0 12px 32px rgba(0,0,0,.18);color:#111827}#aays-security-root.open #aays-security-panel{display:block}.aays-security-title{font-weight:800;margin-bottom:4px}.aays-security-sub,.aays-security-note{font-size:12px;color:#4b5563;margin:6px 0}.aays-security-legend{display:flex;align-items:center;gap:8px;font-size:12px;margin:4px 0}.aays-security-legend span{display:inline-block;width:18px;height:12px;border-radius:3px;border:1px solid rgba(0,0,0,.18)}#aays-security-stat{font-size:12px;font-weight:700;margin-top:8px}.aays-security-popup{font:12px/1.35 Inter,Arial,sans-serif;color:#111827;max-height:430px;overflow:auto}.aays-security-popup-title{font-size:14px;font-weight:800;margin-bottom:7px}.aays-security-popup-row{border-top:1px solid #e5e7eb;padding:4px 0}.aays-security-popup-row b{color:#374151}.aays-security-popup-note{margin-top:7px;font-size:11px;color:#6b7280}
'@
W $JsPath $Js
W $CssPath $Css
W (Join-Path $Web 'data\security_source_manifest.json') '{"source_name":"MISSING_IN_CURRENT_DATA_CONTRACT","note":"Scaffold only; do not fake source/date/evidence."}'
W (Join-Path $Web 'data\security_evidence_manifest.jsonl') '{"evidence":"MISSING_IN_CURRENT_DATA_CONTRACT","note":"Scaffold only"}'
W (Join-Path $Web 'data\security_hash_manifest.csv') 'path,sha256,note'
$nodeOk=$false
try{node --check $JsPath *> (Join-Path $OutDir "node_check_$Stamp.txt"); $nodeOk=($LASTEXITCODE -eq 0)}catch{}
$geoExists=Test-Path $DataPath
$summaryExists=Test-Path $SummaryPath
$contractOk=((Get-Content $JsPath -Raw) -match 'source_date' -and (Get-Content $JsPath -Raw) -match 'calculation_explanation' -and (Get-Content $JsPath -Raw) -match 'accuracy_rating')
$Decision=if($nodeOk -and $geoExists -and $summaryExists -and $contractOk){'FRONTEND_CONTRACT_PATCH_STATIC_READY'}else{'FRONTEND_CONTRACT_PATCH_PARTIAL'}
$Result=[ordered]@{task_id='security-public-safety-frontend-contract-patch-min-20260612';decision=$Decision;node_check=$nodeOk;geojson_exists=$geoExists;summary_exists=$summaryExists;contract_fields_static=$contractOk;app_root=$Repo;db_write=$false;migration=$false;production_deploy=$false;final_ready=$false;complete=$false;next_step='Browser click acceptance still required for FINAL_READY.';finished_at=(Get-Date).ToString('o')}
$Json=Join-Path $Bridge 'ai-results\security_public_safety_frontend_contract_patch_latest.json'
W $Json ($Result|ConvertTo-Json -Depth 8)
$Status=Join-Path $StatusDir 'security_frontend_contract_patch_latest.md'
W $Status ("# Security frontend contract patch`n`ndecision: $Decision`nnode_check: $nodeOk`ngeojson_exists: $geoExists`nsummary_exists: $summaryExists`ncontract_fields_static: $contractOk`nfinal_ready: false`ncomplete: false`ndb_write: false`nmigration: false`nproduction_deploy: false`n")
Copy-Item $Status (Join-Path $ReportDir "security_frontend_contract_patch_$Stamp.md") -Force
W (Join-Path $HbDir 'frontend_patch_latest.md') ("# Security frontend patch heartbeat`n`ndecision: $Decision`nchecked_at: $(Get-Date -Format o)`n")
git -C $Repo add england_map_web/security_overlay.js england_map_web/security_overlay.css england_map_web/data/security_source_manifest.json england_map_web/data/security_evidence_manifest.jsonl england_map_web/data/security_hash_manifest.csv
git -C $Repo commit -m "Apply security frontend contract patch $Stamp" 2>&1|ForEach-Object{L $_}
git -C $Repo push 2>&1|ForEach-Object{L $_}
git -C $Bridge add 'ai-results/security_public_safety_frontend_contract_patch_latest.json' "docs/chatgpt_status/$Page"
git -C $Bridge commit -m "Record security frontend contract patch result $Stamp" 2>&1|ForEach-Object{L $_}
git -C $Bridge push origin main 2>&1|ForEach-Object{L $_}
exit 0
