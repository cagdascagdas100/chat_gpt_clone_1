$Bridge="C:\AAYS_GITHUB_BRIDGE_CLEAN2"
$TaskId="aays-v24-parcel-future-growth-scores-probe"
$ScriptDir="$Bridge\ai-task-scripts"
$Pending="$Bridge\ai-queue\pending"
$Runner="$ScriptDir\portable_queue_runner.ps1"
$Script="$ScriptDir\aays_v24_parcel_future_growth_scores_probe.ps1"
New-Item -ItemType Directory -Force -Path $ScriptDir,$Pending,"$Bridge\ai-results" | Out-Null
$Inner=@'
$ErrorActionPreference="Continue"
$Bridge="C:\AAYS_GITHUB_BRIDGE_CLEAN2"
$RepoUrl="https://github.com/cagdascagdas100/chat_gpt_clone_1.git"
$Stamp=Get-Date -Format "yyyyMMdd_HHmmss"
$Results="$Bridge\ai-results"
$Report="$Results\AAYS_V24_PARCEL_FUTURE_GROWTH_SCORES_PROBE_$Stamp.txt"
$PushRoot="F:\chatgpt\AAYS_TEMP"
if(-not (Test-Path "F:\")){$PushRoot="C:\"}
$PushWork=Join-Path $PushRoot "aays_v24_push_$Stamp"
New-Item -ItemType Directory -Force -Path $Results,$PushRoot | Out-Null
function RunQ($label,$q){ "`n--- $label ---`n$q`n" | Add-Content -Encoding UTF8 $Report; docker exec terrayield_land_postgis psql -U postgres -d terrayield_land -v ON_ERROR_STOP=0 -c $q 2>&1 | Out-String | Add-Content -Encoding UTF8 $Report }
$Port8010=Test-NetConnection -ComputerName localhost -Port 8010 -InformationLevel Quiet
$Port55460=Test-NetConnection -ComputerName localhost -Port 55460 -InformationLevel Quiet
@"
PAGE_KEY=AAYS_SAME_PROJECT_NEW_PAGE
PROJECT=AAYS_TerraYield
TASK=AAYS_V24_PARCEL_FUTURE_GROWTH_SCORES_PROBE
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
$Probe=""
foreach($u in @("http://localhost:8010/api/future-growth/layer","http://localhost:8010/api/future-growth/methodology","http://localhost:8010/openapi.json")){
  try{$r=Invoke-WebRequest -UseBasicParsing -Uri $u -TimeoutSec 15; $Probe += "URL=$u STATUS=$($r.StatusCode) LEN=$($r.Content.Length)`n"}
  catch{$Probe += "URL=$u ERROR=$($_.Exception.Message)`n"}
}
"`nHTTP_PROBE:`n$Probe" | Add-Content -Encoding UTF8 $Report
RunQ "table_counts" "select 'parcel_future_growth_scores' as table_name, count(*) as rows from public.parcel_future_growth_scores union all select 'parcel_future_growth_evidence', count(*) from public.parcel_future_growth_evidence union all select 'future_growth_features', count(*) from public.future_growth_features union all select 'future_growth_sources', count(*) from public.future_growth_sources union all select 'city_growth_vectors', count(*) from public.city_growth_vectors;"
RunQ "score_versions" "select calculation_version, count(*) as rows, min(calculated_at) as min_calculated_at, max(calculated_at) as max_calculated_at from public.parcel_future_growth_scores group by calculation_version order by rows desc limit 50;"
RunQ "score_quality" "select count(*) as total_rows, count(distinct parcel_id) as distinct_parcels, count(*) filter (where score_total is null) as null_score_total, count(*) filter (where future_growth_percent is null) as null_future_growth_percent, count(*) filter (where confidence_score is null) as null_confidence_score from public.parcel_future_growth_scores;"
RunQ "score_sample" "select parcel_id, score_total, future_growth_percent, confidence_score, color_class, calculation_version, calculated_at from public.parcel_future_growth_scores order by calculated_at desc nulls last limit 25;"
RunQ "candidate_version_match" "select count(*) as candidate_version_rows from public.parcel_future_growth_scores where calculation_version='future_growth_v1_real_candidate_fg444_20260602';"
$Progress=86
$State="parcel_future_growth_scores_diagnosed_v24"
"`nFINAL:`nSTATUS=$State`nSUGGESTED_PROGRESS_PERCENT=$Progress" | Add-Content -Encoding UTF8 $Report
Remove-Item $PushWork -Recurse -Force -ErrorAction SilentlyContinue
git clone --filter=blob:none --sparse $RepoUrl $PushWork
if(Test-Path $PushWork){
  Push-Location $PushWork
  git config core.longpaths true
  git sparse-checkout set docs/chatgpt_status
  git checkout main
  git pull --ff-only origin main
  New-Item -ItemType Directory -Force -Path "docs\chatgpt_status" | Out-Null
  Copy-Item $Report "docs\chatgpt_status\AAYS_SAME_PROJECT_NEW_PAGE_v24_parcel_future_growth_scores_probe_$Stamp.txt" -Force
@"
PAGE_KEY: AAYS_SAME_PROJECT_NEW_PAGE
PROJECT: AAYS_TerraYield
STATUS: $State
SUGGESTED_PROGRESS_PERCENT: $Progress
UPDATED_AT: $(Get-Date -Format s)
REPORT_FILE: docs/chatgpt_status/AAYS_SAME_PROJECT_NEW_PAGE_v24_parcel_future_growth_scores_probe_$Stamp.txt
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
  git add docs/chatgpt_status/AAYS_SAME_PROJECT_NEW_PAGE_v24_parcel_future_growth_scores_probe_$Stamp.txt docs/chatgpt_status/AAYS_SAME_PROJECT_NEW_PAGE_latest_result.txt docs/chatgpt_status/AAYS_SAME_PROJECT_NEW_PAGE_BOOK_OUTPUT.txt
  git commit -m "Add AAYS V24 parcel future growth scores probe report"
  git push origin main
  Pop-Location
}
exit 0
'@
$Inner | Set-Content -Encoding UTF8 $Script
$Task=[ordered]@{page_key="AAYS_SAME_PROJECT_NEW_PAGE";project_name="AAYS_TerraYield";id=$TaskId;task_id=$TaskId;script_path=$Script;timeout_seconds=1800;db_write=$false;production_deploy=$false;migration_ddl=$false;fake_data=$false;destructive_git=$false;purpose="read-only probe parcel_future_growth_scores table and future-growth endpoints"}
$Task | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 "$Pending\$TaskId.task.json"
$RunnerActive=@(Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match "portable_queue_runner.ps1" }).Count
if($RunnerActive -eq 0 -and (Test-Path $Runner)){Start-Process powershell -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$Runner`""}
"QUEUED=$TaskId"
"RUNNER_ACTIVE_COUNT=$RunnerActive"
"MANUAL_OUTPUT_PASTE_REQUIRED=false"
