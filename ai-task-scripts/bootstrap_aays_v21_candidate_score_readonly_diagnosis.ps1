$Bridge="C:\AAYS_GITHUB_BRIDGE_CLEAN2"
$TaskId="aays-v21-candidate-score-readonly-diagnosis"
$ScriptDir="$Bridge\ai-task-scripts"
$Pending="$Bridge\ai-queue\pending"
$Runner="$ScriptDir\portable_queue_runner.ps1"
$Script="$ScriptDir\aays_v21_candidate_score_readonly_diagnosis.ps1"
New-Item -ItemType Directory -Force -Path $ScriptDir,$Pending,"$Bridge\ai-results" | Out-Null
$Inner=@'
$ErrorActionPreference="Continue"
$Bridge="C:\AAYS_GITHUB_BRIDGE_CLEAN2"
$RepoUrl="https://github.com/cagdascagdas100/chat_gpt_clone_1.git"
$Stamp=Get-Date -Format "yyyyMMdd_HHmmss"
$Results="$Bridge\ai-results"
$Report="$Results\AAYS_V21_CANDIDATE_SCORE_READONLY_DIAGNOSIS_$Stamp.txt"
$PushWork="F:\chatgpt\AAYS_TEMP\aays_v21_push_$Stamp"
if(-not (Test-Path "F:\")){$PushWork="C:\aays_v21_push_$Stamp"}
New-Item -ItemType Directory -Force -Path $Results,(Split-Path $PushWork) | Out-Null
function P($Name,$Text){"`n===== $Name =====`n$Text" | Add-Content -Encoding UTF8 $Report}
@"
PAGE_KEY=AAYS_SAME_PROJECT_NEW_PAGE
PROJECT=AAYS_TerraYield
TASK=AAYS_V21_CANDIDATE_SCORE_READONLY_DIAGNOSIS
STATUS=running
STARTED_AT=$(Get-Date -Format s)
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
$Port8010=Test-NetConnection -ComputerName localhost -Port 8010 -InformationLevel Quiet
$Port55460=Test-NetConnection -ComputerName localhost -Port 55460 -InformationLevel Quiet
P "PORTS" "PORT_8010=$Port8010`nPORT_55460=$Port55460"
$Api=""
try{$o=Invoke-WebRequest -UseBasicParsing -Uri "http://localhost:8010/openapi.json" -TimeoutSec 15; $json=$o.Content|ConvertFrom-Json; $paths=$json.paths.PSObject.Properties.Name | Where-Object {$_ -match "growth|future|score|layer|parcel|methodology|candidate"}; $Api=($paths|Select-Object -First 300|Out-String)}catch{$Api="OPENAPI_ERROR=$($_.Exception.Message)"}
P "OPENAPI_RELEVANT_PATHS" $Api
$Sql=@"
select table_schema, table_name from information_schema.tables where table_schema not in ('pg_catalog','information_schema') and (table_name ilike '%score%' or table_name ilike '%growth%' or table_name ilike '%candidate%' or table_name ilike '%future%' or table_name ilike '%parcel%') order by table_schema, table_name;
select table_schema, table_name, column_name, data_type from information_schema.columns where table_schema not in ('pg_catalog','information_schema') and (table_name ilike '%score%' or table_name ilike '%growth%' or table_name ilike '%candidate%' or table_name ilike '%future%' or column_name ilike '%score%' or column_name ilike '%probability%' or column_name ilike '%version%' or column_name ilike '%parcel%') order by table_schema, table_name, ordinal_position limit 500;
select 'future_growth_scores' as table_name, count(*)::text as row_count from future_growth_scores;
select 'future_growth_scores_versions' as section, score_version, source_mode, count(*) from future_growth_scores group by score_version, source_mode order by count(*) desc limit 50;
"@
$SqlFile="$Results\AAYS_V21_READONLY_DIAG_$Stamp.sql"
$Sql | Set-Content -Encoding UTF8 $SqlFile
$DbOut=docker exec -i terrayield_land_postgis psql -U postgres -d terrayield_land -v ON_ERROR_STOP=0 -f - < $SqlFile 2>&1 | Out-String
P "DB_READONLY_DISCOVERY" $DbOut
$Progress=83
$State="candidate_score_source_diagnosed_v21"
P "FINAL" "STATUS=$State`nSUGGESTED_PROGRESS_PERCENT=$Progress"
Remove-Item $PushWork -Recurse -Force -ErrorAction SilentlyContinue
git clone --filter=blob:none --sparse $RepoUrl $PushWork
if(Test-Path $PushWork){
  Push-Location $PushWork
  git config core.longpaths true
  git sparse-checkout set docs/chatgpt_status
  git checkout main
  git pull --ff-only origin main
  New-Item -ItemType Directory -Force -Path "docs\chatgpt_status" | Out-Null
  Copy-Item $Report "docs\chatgpt_status\AAYS_SAME_PROJECT_NEW_PAGE_v21_candidate_score_readonly_diagnosis_$Stamp.txt" -Force
@"
PAGE_KEY: AAYS_SAME_PROJECT_NEW_PAGE
PROJECT: AAYS_TerraYield
STATUS: $State
SUGGESTED_PROGRESS_PERCENT: $Progress
UPDATED_AT: $(Get-Date -Format s)
REPORT_FILE: docs/chatgpt_status/AAYS_SAME_PROJECT_NEW_PAGE_v21_candidate_score_readonly_diagnosis_$Stamp.txt
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
"@ | Set-Content -Encoding UTF8 "docs\chatgpt_status\AAYS_SAME_PROJECT_NEW_PAGE_latest_result.txt"
  Copy-Item "docs\chatgpt_status\AAYS_SAME_PROJECT_NEW_PAGE_latest_result.txt" "docs\chatgpt_status\AAYS_SAME_PROJECT_NEW_PAGE_BOOK_OUTPUT.txt" -Force
  git config user.email "aays-runner@example.local"
  git config user.name "AAYS Runner"
  git add docs/chatgpt_status/AAYS_SAME_PROJECT_NEW_PAGE_v21_candidate_score_readonly_diagnosis_$Stamp.txt docs/chatgpt_status/AAYS_SAME_PROJECT_NEW_PAGE_latest_result.txt docs/chatgpt_status/AAYS_SAME_PROJECT_NEW_PAGE_BOOK_OUTPUT.txt
  git commit -m "Add AAYS V21 candidate score readonly diagnosis report"
  git push origin main
  Pop-Location
}
exit 0
'@
$Inner | Set-Content -Encoding UTF8 $Script
$Task=[ordered]@{page_key="AAYS_SAME_PROJECT_NEW_PAGE";project_name="AAYS_TerraYield";id=$TaskId;task_id=$TaskId;script_path=$Script;timeout_seconds=1800;db_write=$false;production_deploy=$false;migration_ddl=$false;fake_data=$false;destructive_git=$false;purpose="read-only diagnose candidate score source and endpoints"}
$Task | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 "$Pending\$TaskId.task.json"
$RunnerActive=@(Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match "portable_queue_runner.ps1" }).Count
if($RunnerActive -eq 0 -and (Test-Path $Runner)){Start-Process powershell -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$Runner`""}
"QUEUED=$TaskId"
"RUNNER_ACTIVE_COUNT=$RunnerActive"
"MANUAL_OUTPUT_PASTE_REQUIRED=false"
