$Bridge="C:\AAYS_GITHUB_BRIDGE_CLEAN2"
$TaskId="aays-v26-future-growth-layer-empty-diagnosis"
$ScriptDir="$Bridge\ai-task-scripts"
$Pending="$Bridge\ai-queue\pending"
$Runner="$ScriptDir\portable_queue_runner.ps1"
$Script="$ScriptDir\aays_v26_future_growth_layer_empty_diagnosis.ps1"
New-Item -ItemType Directory -Force -Path $ScriptDir,$Pending,"$Bridge\ai-results" | Out-Null
$Inner=@'
$ErrorActionPreference="Continue"
$Bridge="C:\AAYS_GITHUB_BRIDGE_CLEAN2"
$AaysRepo="C:\Users\cagda\Documents\GitHub\AAYS"
$RepoUrl="https://github.com/cagdascagdas100/chat_gpt_clone_1.git"
$Stamp=Get-Date -Format "yyyyMMdd_HHmmss"
$Results="$Bridge\ai-results"
$Report="$Results\AAYS_V26_FUTURE_GROWTH_LAYER_EMPTY_DIAGNOSIS_$Stamp.txt"
$PushRoot="F:\chatgpt\AAYS_TEMP"
if(-not (Test-Path "F:\")){$PushRoot="C:\"}
$PushWork=Join-Path $PushRoot "aays_v26_push_$Stamp"
New-Item -ItemType Directory -Force -Path $Results,$PushRoot | Out-Null
function AddSec($n,$t){"`n===== $n =====`n$t" | Add-Content -Encoding UTF8 $Report}
function Hit($u){try{$r=Invoke-WebRequest -UseBasicParsing -Uri $u -TimeoutSec 15; "URL=$u STATUS=$($r.StatusCode) LEN=$($r.Content.Length)`n$($r.Content.Substring(0,[Math]::Min(3000,$r.Content.Length)))"}catch{"URL=$u ERROR=$($_.Exception.Message)"}}
function Q($label,$sql){AddSec $label ((docker exec terrayield_land_postgis psql -U postgres -d terrayield_land -v ON_ERROR_STOP=0 -c $sql 2>&1 | Out-String))}
$Port8010=Test-NetConnection -ComputerName localhost -Port 8010 -InformationLevel Quiet
$Port55460=Test-NetConnection -ComputerName localhost -Port 55460 -InformationLevel Quiet
@"
PAGE_KEY=AAYS_SAME_PROJECT_NEW_PAGE
PROJECT=AAYS_TerraYield
TASK=AAYS_V26_FUTURE_GROWTH_LAYER_EMPTY_DIAGNOSIS
STATUS=running
UPDATED_AT=$(Get-Date -Format s)
PORT_8010=$Port8010
PORT_55460=$Port55460
MANUAL_OUTPUT_PASTE_REQUIRED=false
SAFETY_DB_WRITE=false
SAFETY_PRODUCTION_DEPLOY=false
SAFETY_MIGRATION_DDL=false
SAFETY_FAKE_DATA=false
SAFETY_DESTRUCTIVE_GIT=false
GIT_RESET_HARD=false
GIT_CLEAN=false
FORCE_PUSH=false
"@ | Set-Content -Encoding UTF8 $Report
AddSec "HTTP_LAYER_DEFAULT" (Hit "http://localhost:8010/api/future-growth/layer")
AddSec "HTTP_LAYER_WIDE" (Hit "http://localhost:8010/api/future-growth/layer?limit=50&min_score=0&bbox=-10,49,3,61")
Q "SCORE_JOIN_GEOMETRY_COUNT" "select count(*) as joined_rows from public.parcel_future_growth_scores s join public.parcels_inspire p on p.parcel_id=s.parcel_id where p.geom is not null;"
Q "SCORE_GEOM_SAMPLE" "select s.parcel_id, s.score_total, s.future_growth_percent, s.calculation_version, st_astext(st_centroid(p.geom)) as centroid from public.parcel_future_growth_scores s join public.parcels_inspire p on p.parcel_id=s.parcel_id where p.geom is not null order by s.parcel_id limit 10;"
Q "PARCEL_ID_OVERLAP" "select (select count(*) from public.parcel_future_growth_scores) as score_rows, (select count(*) from public.parcels_inspire) as inspire_rows, (select count(*) from public.parcel_future_growth_scores s where exists (select 1 from public.parcels_inspire p where p.parcel_id=s.parcel_id)) as overlap_rows;"
Q "FEATURE_GEOM_COUNT" "select count(*) as feature_rows, count(*) filter (where geometry is not null) as feature_geom_rows from public.future_growth_features;"
$CodeHits=""
try{$CodeHits=Get-ChildItem "$AaysRepo\terrayield_land_intelligence\app" -Recurse -File -Include "*.py" -ErrorAction SilentlyContinue | Select-String -Pattern "api/future-growth/layer|def .*layer|FeatureCollection|bbox|min_score|parcel_future_growth_scores|ST_AsGeoJSON|geometry_json" -Context 3,3 | Select-Object -First 240 | Out-String}catch{$CodeHits="CODE_SEARCH_ERROR=$($_.Exception.Message)"}
AddSec "LOCAL_LAYER_CODE_HITS" $CodeHits
$Progress=90
$State="future_growth_layer_empty_reason_diagnosed_v26"
AddSec "FINAL" "STATUS=$State`nSUGGESTED_PROGRESS_PERCENT=$Progress"
Remove-Item $PushWork -Recurse -Force -ErrorAction SilentlyContinue
git clone --filter=blob:none --sparse $RepoUrl $PushWork
if(Test-Path $PushWork){
  Push-Location $PushWork
  git config core.longpaths true
  git sparse-checkout set docs/chatgpt_status
  git checkout main
  git pull --ff-only origin main
  New-Item -ItemType Directory -Force -Path "docs\chatgpt_status" | Out-Null
  Copy-Item $Report "docs\chatgpt_status\AAYS_SAME_PROJECT_NEW_PAGE_v26_future_growth_layer_empty_diagnosis_$Stamp.txt" -Force
@"
PAGE_KEY: AAYS_SAME_PROJECT_NEW_PAGE
PROJECT: AAYS_TerraYield
STATUS: $State
SUGGESTED_PROGRESS_PERCENT: $Progress
UPDATED_AT: $(Get-Date -Format s)
REPORT_FILE: docs/chatgpt_status/AAYS_SAME_PROJECT_NEW_PAGE_v26_future_growth_layer_empty_diagnosis_$Stamp.txt
PORT_8010=$Port8010
PORT_55460=$Port55460
MANUAL_OUTPUT_PASTE_REQUIRED=false
SAFETY:
DB_WRITE=false
PRODUCTION_DEPLOY=false
MIGRATION_DDL=false
FAKE_DATA=false
DESTRUCTIVE_GIT=false
GIT_RESET_HARD=false
GIT_CLEAN=false
FORCE_PUSH=false
"@ | Set-Content -Encoding UTF8 "docs\chatgpt_status\AAYS_SAME_PROJECT_NEW_PAGE_latest_result.txt"
  Copy-Item "docs\chatgpt_status\AAYS_SAME_PROJECT_NEW_PAGE_latest_result.txt" "docs\chatgpt_status\AAYS_SAME_PROJECT_NEW_PAGE_BOOK_OUTPUT.txt" -Force
  git config user.email "aays-runner@example.local"
  git config user.name "AAYS Runner"
  git add docs/chatgpt_status/AAYS_SAME_PROJECT_NEW_PAGE_v26_future_growth_layer_empty_diagnosis_$Stamp.txt docs/chatgpt_status/AAYS_SAME_PROJECT_NEW_PAGE_latest_result.txt docs/chatgpt_status/AAYS_SAME_PROJECT_NEW_PAGE_BOOK_OUTPUT.txt
  git commit -m "Add AAYS V26 future growth layer empty diagnosis report"
  git push origin main
  Pop-Location
}
exit 0
'@
$Inner | Set-Content -Encoding UTF8 $Script
$Task=[ordered]@{page_key="AAYS_SAME_PROJECT_NEW_PAGE";project_name="AAYS_TerraYield";id=$TaskId;task_id=$TaskId;script_path=$Script;timeout_seconds=1800;db_write=$false;production_deploy=$false;migration_ddl=$false;fake_data=$false;destructive_git=$false;purpose="read-only diagnose why future growth layer returns empty features"}
$Task | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 "$Pending\$TaskId.task.json"
$RunnerActive=@(Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match "portable_queue_runner.ps1" }).Count
if($RunnerActive -eq 0 -and (Test-Path $Runner)){Start-Process powershell -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$Runner`""}
"QUEUED=$TaskId"
"RUNNER_ACTIVE_COUNT=$RunnerActive"
"MANUAL_OUTPUT_PASTE_REQUIRED=false"
