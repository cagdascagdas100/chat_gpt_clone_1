$ErrorActionPreference='Continue'
$TaskId='chatgpt-frontend-layer-integration-verify-20260524'
$Bridge='C:\AAYS_GITHUB_BRIDGE_CLEAN2'
$Project='C:\Users\cagda\Documents\GitHub\AAYS'
$Web=Join-Path $Project 'england_map_web'
$App=Join-Path $Web 'app.js'
$R=Join-Path $Bridge 'ai-results'
New-Item -ItemType Directory -Force -Path $R | Out-Null
$checks=@()
function AddCheck($name,$ok,$detail){$script:checks += [ordered]@{name=$name;ok=[bool]$ok;detail=$detail}}
AddCheck 'project_root_exists' (Test-Path $Project) $Project
AddCheck 'web_root_exists' (Test-Path $Web) $Web
AddCheck 'app_js_exists' (Test-Path $App) $App
$txt=''
if(Test-Path $App){try{$txt=Get-Content $App -Raw -ErrorAction Stop}catch{$txt=''}}
$patterns=@('EMISSIONS_CONTROL_MODE','air.png','topografic_map.png','land_use','setEmissionsLayerVisibility','toggleEmissionsLayer','emissionsToggle','requiredModes')
foreach($p in $patterns){AddCheck ('contains_'+$p) ($txt.Contains($p)) $p}
$air=Join-Path $Web 'air.png'
$topo=Join-Path $Web 'topografic_map.png'
AddCheck 'air_png_exists' (Test-Path $air) $air
AddCheck 'topografic_map_png_exists' (Test-Path $topo) $topo
$nodeCheck='not_run'
if(Test-Path $App){try{Push-Location $Project; node --check '.\england_map_web\app.js' 2>&1 | Set-Variable -Name nodeOut; $nodeCode=$LASTEXITCODE; Pop-Location; $nodeCheck=($nodeOut -join "`n"); AddCheck 'node_check_app_js' ($nodeCode -eq 0) $nodeCheck}catch{AddCheck 'node_check_app_js' $false $_.Exception.Message}}
try{$resp=Invoke-WebRequest -Uri 'http://127.0.0.1:8010/england_map_web/' -UseBasicParsing -TimeoutSec 5; AddCheck 'local_frontend_200' ($resp.StatusCode -eq 200) ('status='+$resp.StatusCode)}catch{AddCheck 'local_frontend_200' $false $_.Exception.Message}
try{$resp=Invoke-WebRequest -Uri 'http://127.0.0.1:8010/england_map_web/air.png' -UseBasicParsing -TimeoutSec 5; AddCheck 'air_png_http_200' ($resp.StatusCode -eq 200) ('status='+$resp.StatusCode)}catch{AddCheck 'air_png_http_200' $false $_.Exception.Message}
try{$resp=Invoke-WebRequest -Uri 'http://127.0.0.1:8010/england_map_web/topografic_map.png' -UseBasicParsing -TimeoutSec 5; AddCheck 'topografic_map_http_200' ($resp.StatusCode -eq 200) ('status='+$resp.StatusCode)}catch{AddCheck 'topografic_map_http_200' $false $_.Exception.Message}
$failed=@($checks|Where-Object{-not $_.ok})
$status=if($failed.Count -eq 0){'frontend_layer_integration_verified'}else{'frontend_layer_integration_needs_review'}
$progress=if($failed.Count -eq 0){100}else{95}
$result=[ordered]@{task_id=$TaskId;status=$status;overall_progress=$progress;checks=$checks;failed=$failed;db_write=$false;production_deploy=$false;fake_data=$false;paths=[ordered]@{project=$Project;web=$Web;app_js=$App;air_png=$air;topografic_map_png=$topo}}
$result|ConvertTo-Json -Depth 8|Set-Content -Encoding UTF8 (Join-Path $R 'chatgpt_frontend_layer_integration_verify_20260524.result.json')
@('# ChatGPT Frontend Layer Integration Verify','status='+$status,'overall_progress='+$progress,'failed_count='+$failed.Count,'app_js='+$App,'DB_WRITE=false','PRODUCTION_DEPLOY=false','FAKE_DATA=false')|Set-Content -Encoding UTF8 (Join-Path $R 'chatgpt_frontend_layer_integration_verify_20260524.report.md')
Start-Sleep -Seconds 600
exit 0
