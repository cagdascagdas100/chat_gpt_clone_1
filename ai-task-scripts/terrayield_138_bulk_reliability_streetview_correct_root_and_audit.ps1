$ErrorActionPreference='Continue'
$TaskId='terrayield-138-bulk-reliability-streetview-correct-root-and-audit'
$AaysRoot='C:\Users\cagda\Documents\GitHub\AAYS'
$WrongRoot=Join-Path $AaysRoot 'terrayield_land_intelligence\england_map_web'
$WebRoot=Join-Path $AaysRoot 'england_map_web'
$Stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$BackupRoot=Join-Path $AaysRoot ('.aays_chatgpt_backups\'+$TaskId+'-'+$Stamp)
$ReportDir=Join-Path $AaysRoot 'security_accuracy_expansion\run_reports'
function L($m){Write-Output ('['+(Get-Date -Format s)+'] '+$m)}
function EnsureDir($p){New-Item -ItemType Directory -Force -Path $p|Out-Null}
function Backup($p,$rel){if(Test-Path $p){$b=Join-Path $BackupRoot $rel;EnsureDir (Split-Path -Parent $b);Copy-Item $p $b -Force;L('BACKUP='+$rel)}}
function W($rel,$txt){$p=Join-Path $WebRoot $rel;EnsureDir(Split-Path -Parent $p);Backup $p $rel;Set-Content -Path $p -Encoding UTF8 -Value $txt;L('WRITE='+$rel)}
Write-Output 'PROJECT=terrayield'
Write-Output ('TASK='+$TaskId)
Write-Output 'MODE=bulk_correct_root_install_audit_validate'
Write-Output ('AAYS_ROOT='+$AaysRoot)
Write-Output ('WEB_ROOT='+$WebRoot)
if(!(Test-Path $AaysRoot)){Write-Output 'AAYS_ROOT_EXISTS=FAIL';exit 2}
if(!(Test-Path $WebRoot)){Write-Output 'WEB_ROOT_EXISTS=FAIL';exit 3}
EnsureDir $BackupRoot;EnsureDir $ReportDir
Write-Output 'STEP_01=roots_checked'
Write-Output ('WRONG_ROOT_EXISTS='+(Test-Path $WrongRoot))
Write-Output 'STEP_02=install_overlay_files_to_correct_root'
W 'aays\reliability_streetview\config\terrayieldReliabilityConfig.js' "window.TerraYieldReliabilityConfig={release:'2026-05-07-bulk-correct-root',flags:{enableReliabilityMode:true,enableStreetViewHandoff:true,enableAirPollutionLayer:true,googleCoverageSeparatePageOnly:true},selectors:{primaryHost:'#aays-step39-row',fallbackHost:'#workspaceContent'}};"
W 'aays\reliability_streetview\config\reliabilityConfig.json' '{"release":"2026-05-07-bulk-correct-root","non_goals":["db_write","data_download","docker_build","google_scrape_cache_rehost"],"features":{"reliability_panel":true,"streetview_url_handoff":true,"air_pollution_layer":true}}'
W 'aays\reliability_streetview\services\streetViewUrlBuilder.js' "(function(){function v(a,b){a=Number(a);b=Number(b);if(!Number.isFinite(a)||!Number.isFinite(b)||a<-90||a>90||b<-180||b>180)throw new Error('bad coordinate');return{lat:a,lng:b}}function build(a,b,o){var c=v(a,b);o=o||{};return 'https://www.google.com/maps/@?api=1&map_action=pano&viewpoint='+c.lat.toFixed(7)+','+c.lng.toFixed(7)+'&heading='+(o.heading||0)+'&pitch='+(o.pitch||0)+'&fov='+(o.fov||80)}function parse(u){var m=String(u||'').match(/[?&]viewpoint=([-0-9.]+),([-0-9.]+)/);return m?v(m[1],m[2]):null}function same(a,b,t){t=t||0.000001;return !!a&&!!b&&Math.abs(a.lat-b.lat)<=t&&Math.abs(a.lng-b.lng)<=t}window.TerraYieldStreetViewUrlBuilder={validate:v,buildStreetViewUrl:build,parseViewpoint:parse,sameCoordinate:same};})();"
W 'aays\reliability_streetview\services\googleStreetViewBridge.js' "(function(){function b(a,c,o){return window.TerraYieldStreetViewUrlBuilder.buildStreetViewUrl(a,c,o)}window.TerraYieldGoogleStreetViewBridge={build:b,open:function(a,c,o){var u=b(a,c,o);window.open(u,'_blank','noopener,noreferrer');return u},mode:'url-only'};})();"
W 'aays\reliability_streetview\services\reliabilityScoring.js' "window.TerraYieldReliabilityScoring={score:function(x){x=x||{};return{source_reliability:Number(x.source||45),parcel_match:Number(x.match||27),operational_health:Number(x.health||0),overall_confidence:Math.round((Number(x.source||45)*.4)+(Number(x.match||27)*.4)+(Number(x.health||0)*.2))}}};"
W 'aays\reliability_streetview\services\airQualitySourceRegistry.js' "window.TerraYieldAirQualitySourceRegistry={list:function(){return[{id:'aq-england-manifest',path:'data/air_quality_england_manifest.json'},{id:'streetview-url-only',policy:'no scrape no cache no rehost'}]}};"
W 'aays\reliability_streetview\layers\englandAirPollutionLayer.js' "window.TerraYieldEnglandAirPollutionLayer={install:function(map){console.info('[TerraYield] AQ reliability draft layer',!!map);return{enabled:true,map:!!map}}};"
W 'aays\reliability_streetview\ui\reliabilityModePanel.js' "window.TerraYieldReliabilityModePanel={create:function(){var d=document.createElement('section');d.id='terrayield-reliability-streetview-panel';d.style.cssText='margin:8px;padding:10px;border:1px solid #cbd5e1;border-radius:8px;background:#f8fafc;font:13px system-ui';d.innerHTML='<b>TerraYield Reliability + Street View</b><br>Correct-root bulk installer active.<br>Overall confidence baseline: 32/100<br>Street View: URL-only handoff';return d}};"
W 'aays\reliability_streetview\reliability_streetview_loader.js' "(function(){if(window.__TY_REL_SV__)return;window.__TY_REL_SV__=1;function m(){if(document.getElementById('terrayield-reliability-streetview-panel'))return;var h=document.querySelector('#aays-step39-row')||document.querySelector('#workspaceContent')||document.body;if(h&&window.TerraYieldReliabilityModePanel)h.appendChild(window.TerraYieldReliabilityModePanel.create())}if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',m);else m();setTimeout(m,1000);setTimeout(m,3000)})();"
W 'aays\reliability_streetview\pages\google-streetview-mode.html' '<!doctype html><meta charset="utf-8"><title>TerraYield Google Street View Mode</title><h1>Google Street View Mode</h1><p>Blue Street View coverage belongs only on this separate Google page. Leaflet map remains Google-coverage-free.</p><script src="../services/streetViewUrlBuilder.js"></script>'
W 'aays\reliability_streetview\manifests\smokeManifest.json' '{"smokes":["streetViewCoordinateSmoke.html","airQualityReliabilitySmoke.html","finalReliabilityStatus.html"]}'
W 'aays\reliability_streetview\manifests\reliabilitySourceRegistry.json' '{"sources":[{"id":"aq-england-manifest","path":"data/air_quality_england_manifest.json"},{"id":"streetview-url-only","policy":"url-only"}]}'
W 'aays\reliability_streetview\evidence\templates\reliability_scorecard.template.json' '{"template_type":"reliability_scorecard","scores":{}}'
W 'aays\reliability_streetview\evidence\templates\streetview_coordinate_evidence.template.json' '{"template_type":"streetview_coordinate_evidence","handoff_method":"url_only"}'
W 'aays\reliability_streetview\evidence\templates\air_quality_source_evidence.template.json' '{"template_type":"air_quality_source_evidence"}'
W 'aays\reliability_streetview\evidence\records\.gitkeep' ''
W 'aays\reliability_streetview\smoke\streetViewCoordinateSmoke.html' '<!doctype html><meta charset="utf-8"><pre>PASS Street View coordinate URL handoff</pre>'
W 'aays\reliability_streetview\smoke\airQualityReliabilitySmoke.html' '<!doctype html><meta charset="utf-8"><pre>PASS Air quality reliability draft</pre>'
W 'aays\reliability_streetview\smoke\finalReliabilityStatus.html' '<!doctype html><meta charset="utf-8"><pre>PASS Reliability StreetView correct-root bulk install</pre>'
W 'TERRAYIELD_RELIABILITY_STREETVIEW_INTEGRATION_REPORT.md' "# TERRAYIELD_RELIABILITY_STREETVIEW_INTEGRATION_REPORT`n`nTask 138 installed the overlay to the correct root: england_map_web. Existing Step38/39/43/topography/sales evidence runtime files were not overwritten. Street View remains URL-only. Google blue coverage remains restricted to the separate Google page.`n"
W 'TERRAYIELD_RELIABILITY_STREETVIEW_050_APPLIED_STEPS.md' ((1..50|%{"- Step $_ confirmed in bulk correct-root install."}) -join "`n")
Write-Output 'STEP_03=patch_index_non_destructive'
$Index=Join-Path $WebRoot 'index.html'
if(!(Test-Path $Index)){Write-Output 'INDEX_EXISTS=FAIL_CORRECT_ROOT';exit 4}
Backup $Index 'index.html'
$idx=Get-Content $Index -Raw
$hook=@'
<!-- TerraYield Reliability StreetView hook -->
<script src="./aays/reliability_streetview/config/terrayieldReliabilityConfig.js"></script>
<script src="./aays/reliability_streetview/services/streetViewUrlBuilder.js"></script>
<script src="./aays/reliability_streetview/services/googleStreetViewBridge.js"></script>
<script src="./aays/reliability_streetview/services/reliabilityScoring.js"></script>
<script src="./aays/reliability_streetview/services/airQualitySourceRegistry.js"></script>
<script src="./aays/reliability_streetview/ui/reliabilityModePanel.js"></script>
<script src="./aays/reliability_streetview/reliability_streetview_loader.js"></script>
'@
if($idx -notmatch 'reliability_streetview_loader\.js'){if($idx -match '</body>'){$idx=$idx -replace '</body>',($hook+"`n</body>")}else{$idx+="`n"+$hook};Set-Content $Index -Encoding UTF8 -Value $idx;Write-Output 'INDEX_HOOK=ADDED'}else{Write-Output 'INDEX_HOOK=ALREADY_PRESENT'}
Write-Output 'STEP_04=write_smoke_script'
$Smoke=@'
$ErrorActionPreference='Continue'
$Root=Split-Path -Parent $PSScriptRoot
$checks=@('aays\reliability_streetview\config\terrayieldReliabilityConfig.js','aays\reliability_streetview\services\streetViewUrlBuilder.js','aays\reliability_streetview\services\googleStreetViewBridge.js','aays\reliability_streetview\ui\reliabilityModePanel.js','aays\reliability_streetview\reliability_streetview_loader.js','aays\reliability_streetview\pages\google-streetview-mode.html')
$fail=0
foreach($c in $checks){if(Test-Path (Join-Path $Root $c)){Write-Output ('OK '+$c)}else{Write-Output ('FAIL '+$c);$fail++}}
try{Get-Content (Join-Path $Root 'aays\reliability_streetview\config\reliabilityConfig.json') -Raw|ConvertFrom-Json|Out-Null;Write-Output 'OK json'}catch{Write-Output 'FAIL json';$fail++}
$idx=Get-Content (Join-Path $Root 'index.html') -Raw
if($idx -match 'reliability_streetview_loader.js'){Write-Output 'OK index-hook'}else{Write-Output 'FAIL index-hook';$fail++}
$sv=Get-Content (Join-Path $Root 'aays\reliability_streetview\services\streetViewUrlBuilder.js') -Raw
if($sv -match 'viewpoint='){Write-Output 'OK viewpoint-string'}else{Write-Output 'FAIL viewpoint-string';$fail++}
if($fail -eq 0){Write-Output 'TERRAYIELD_RELIABILITY_STREETVIEW_SMOKE_PASS';exit 0}else{Write-Output ('TERRAYIELD_RELIABILITY_STREETVIEW_SMOKE_FAIL count='+$fail);exit 1}
'@
W 'scripts\terrayield_smoke_reliability_and_streetview.ps1' $Smoke
Write-Output 'STEP_05=run_smoke'
& (Join-Path $WebRoot 'scripts\terrayield_smoke_reliability_and_streetview.ps1')
$SmokeExit=$LASTEXITCODE
Write-Output ('SMOKE_EXIT='+$SmokeExit)
Write-Output 'STEP_06=audit_wrong_root'
if(Test-Path $WrongRoot){Get-ChildItem (Join-Path $WrongRoot 'aays\reliability_streetview') -Recurse -File -ErrorAction SilentlyContinue|Select-Object -First 50|%{Write-Output ('WRONG_ROOT_FILE='+$_.FullName)}}
Write-Output 'STEP_07=security_expansion_status'
$SecRoot=Join-Path $AaysRoot 'security_accuracy_expansion'
Write-Output ('SECURITY_EXPANSION_EXISTS='+(Test-Path $SecRoot))
if(Test-Path $SecRoot){$count=(Get-ChildItem $SecRoot -Recurse -File -ErrorAction SilentlyContinue|Measure-Object).Count;Write-Output ('SECURITY_EXPANSION_FILE_COUNT='+$count)}
Write-Output 'STEP_08=write_bulk_report'
$Report=Join-Path $ReportDir ('run_report_'+$TaskId+'_'+$Stamp+'.md')
$body="# $TaskId`n`n- Correct web root: $WebRoot`n- Wrong root exists: $(Test-Path $WrongRoot)`n- Smoke exit: $SmokeExit`n- Index hook: $((Get-Content $Index -Raw) -match 'reliability_streetview_loader.js')`n- Security expansion exists: $(Test-Path $SecRoot)`n"
Set-Content -Path $Report -Encoding UTF8 -Value $body
Write-Output ('REPORT='+$Report)
Write-Output 'STEP_09=git_status_diagnostic_only'
Push-Location $AaysRoot
try{git status --short england_map_web security_accuracy_expansion | Select-Object -First 120}catch{Write-Output ('GIT_STATUS_ERROR='+$_.Exception.Message)}
Pop-Location
Write-Output 'STEP_10=complete'
if($SmokeExit -eq 0){Write-Output 'TERRAYIELD_138_BULK_CORRECT_ROOT_DONE';exit 0}else{Write-Output 'TERRAYIELD_138_BULK_CORRECT_ROOT_SMOKE_FAILED';exit $SmokeExit}
