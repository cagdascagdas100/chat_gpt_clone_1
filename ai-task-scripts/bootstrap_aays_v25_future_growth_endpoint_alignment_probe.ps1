$Bridge="C:\AAYS_GITHUB_BRIDGE_CLEAN2"
$TaskId="aays-v25-future-growth-endpoint-alignment-probe"
$ScriptDir="$Bridge\ai-task-scripts"
$Pending="$Bridge\ai-queue\pending"
$Runner="$ScriptDir\portable_queue_runner.ps1"
$Script="$ScriptDir\aays_v25_future_growth_endpoint_alignment_probe.ps1"
New-Item -ItemType Directory -Force -Path $ScriptDir,$Pending,"$Bridge\ai-results" | Out-Null
$Inner=@'
$ErrorActionPreference="Continue"
$Bridge="C:\AAYS_GITHUB_BRIDGE_CLEAN2"
$AaysRepo="C:\Users\cagda\Documents\GitHub\AAYS"
$RepoUrl="https://github.com/cagdascagdas100/chat_gpt_clone_1.git"
$Stamp=Get-Date -Format "yyyyMMdd_HHmmss"
$Results="$Bridge\ai-results"
$Report="$Results\AAYS_V25_FUTURE_GROWTH_ENDPOINT_ALIGNMENT_PROBE_$Stamp.txt"
$PushRoot="F:\chatgpt\AAYS_TEMP"
if(-not (Test-Path "F:\")){$PushRoot="C:\"}
$PushWork=Join-Path $PushRoot "aays_v25_push_$Stamp"
New-Item -ItemType Directory -Force -Path $Results,$PushRoot | Out-Null
function AddSec($n,$t){"`n===== $n =====`n$t" | Add-Content -Encoding UTF8 $Report}
function Hit($u){try{$r=Invoke-WebRequest -UseBasicParsing -Uri $u -TimeoutSec 15; "URL=$u STATUS=$($r.StatusCode) LEN=$($r.Content.Length)`n$($r.Content.Substring(0,[Math]::Min(2000,$r.Content.Length)))"}catch{"URL=$u ERROR=$($_.Exception.Message)"}}
$Port8010=Test-NetConnection -ComputerName localhost -Port 8010 -InformationLevel Quiet
$Port55460=Test-NetConnection -ComputerName localhost -Port 55460 -InformationLevel Quiet
@"
PAGE_KEY=AAYS_SAME_PROJECT_NEW_PAGE
PROJECT=AAYS_TerraYield
TASK=AAYS_V25_FUTURE_GROWTH_ENDPOINT_ALIGNMENT_PROBE
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
$DbOut=""
foreach($q in @(
"select calculation_version, count(*) from public.parcel_future_growth_scores group by calculation_version order by count(*) desc;",
"select parcel_id from public.parcel_future_growth_scores order by calculated_at desc nulls last limit 5;",
"select min(parcel_id), max(parcel_id), count(distinct parcel_id) from public.parcel_future_growth_scores;",
"select count(*) as layer_feature_count from public.future_growth_features;"
)){ $DbOut += "`n--- QUERY ---`n$q`n"; $DbOut += (docker exec terrayield_land_postgis psql -U postgres -d terrayield_land -v ON_ERROR_STOP=0 -c $q 2>&1 | Out-String) }
AddSec "DB_VERSION_AND_SAMPLE" $DbOut
AddSec "HTTP_LAYER" (Hit "http://localhost:8010/api/future-growth/layer")
AddSec "HTTP_METHODOLOGY" (Hit "http://localhost:8010/api/future-growth/methodology")
foreach($pid in @(300,299,1)){
  AddSec "HTTP_PARCEL_$pid" (Hit "http://localhost:8010/api/future-growth/parcels/$pid")
  AddSec "HTTP_UI_SCORE_$pid" (Hit "http://localhost:8010/parcels/$pid/future-growth-score")
  AddSec "HTTP_EVIDENCE_$pid" (Hit "http://localhost:8010/api/future-growth/parcels/$pid/evidence")
}
$CodeHits=""
try{$CodeHits=Get-ChildItem "$AaysRepo\terrayield_land_intelligence" -Recurse -File -Include "*.py" -ErrorAction SilentlyContinue | Select-String -Pattern "future_growth_v1_real_candidate_fg444_20260602|future_growth_v1|parcel_future_growth_scores|future-growth/layer|future-growth-score" -Context 2,2 | Select-Object -First 180 | Out-String}catch{$CodeHits="CODE_SEARCH_ERROR=$($_.Exception.Message)"}
AddSec "LOCAL_CODE_HITS" $CodeHits
$Progress=88
$State="future_growth_endpoint_alignment_diagnosed_v25"
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
  Copy-Item $Report "docs\chatgpt_status\AAYS_SAME_PROJECT_NEW_PAGE_v25_future_growth_endpoint_alignment_probe_$Stamp.txt" -Force
@"
PAGE_KEY: AAYS_SAME_PROJECT_NEW_PAGE
PROJECT: AAYS_TerraYield
STATUS: $State
SUGGESTED_PROGRESS_PERCENT: $Progress
UPDATED_AT: $(Get-Date -Format s)
REPORT_FILE: docs/chatgpt_status/AAYS_SAME_PROJECT_NEW_PAGE_v25_future_growth_endpoint_alignment_probe_$Stamp.txt
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
  git add docs/chatgpt_status/AAYS_SAME_PROJECT_NEW_PAGE_v25_future_growth_endpoint_alignment_probe_$Stamp.txt docs/chatgpt_status/AAYS_SAME_PROJECT_NEW_PAGE_latest_result.txt docs/chatgpt_status/AAYS_SAME_PROJECT_NEW_PAGE_BOOK_OUTPUT.txt
  git commit -m "Add AAYS V25 future growth endpoint alignment report"
  git push origin main
  Pop-Location
}
exit 0
'@
$Inner | Set-Content -Encoding UTF8 $Script
$Task=[ordered]@{page_key="AAYS_SAME_PROJECT_NEW_PAGE";project_name="AAYS_TerraYield";id=$TaskId;task_id=$TaskId;script_path=$Script;timeout_seconds=1800;db_write=$false;production_deploy=$false;migration_ddl=$false;fake_data=$false;destructive_git=$false;purpose="read-only diagnose future growth endpoint and score-version alignment"}
$Task | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 "$Pending\$TaskId.task.json"
$RunnerActive=@(Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match "portable_queue_runner.ps1" }).Count
if($RunnerActive -eq 0 -and (Test-Path $Runner)){Start-Process powershell -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$Runner`""}
"QUEUED=$TaskId"
"RUNNER_ACTIVE_COUNT=$RunnerActive"
"MANUAL_OUTPUT_PASTE_REQUIRED=false"
