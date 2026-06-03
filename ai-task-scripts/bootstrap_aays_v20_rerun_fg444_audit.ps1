$Bridge="C:\AAYS_GITHUB_BRIDGE_CLEAN2"
$TaskId="aays-v20-rerun-fg444-audit-api-open"
$ScriptDir="$Bridge\ai-task-scripts"
$Pending="$Bridge\ai-queue\pending"
$Runner="$ScriptDir\portable_queue_runner.ps1"
$Script="$ScriptDir\aays_v20_rerun_fg444_audit_api_open.ps1"
New-Item -ItemType Directory -Force -Path $ScriptDir,$Pending,"$Bridge\ai-results" | Out-Null
$Inner=@'
$ErrorActionPreference="Continue"
$Bridge="C:\AAYS_GITHUB_BRIDGE_CLEAN2"
$AaysRepo="C:\Users\cagda\Documents\GitHub\AAYS"
$RepoUrl="https://github.com/cagdascagdas100/chat_gpt_clone_1.git"
$Stamp=Get-Date -Format "yyyyMMdd_HHmmss"
$Results="$Bridge\ai-results"
$StorageRoot="$Bridge\fg444_storage\future_growth"
$AuditDir="$StorageRoot\audit"
$SafeAudit="$Bridge\ai-task-scripts\FG444_01_READONLY_AUDIT_LOCAL_SAFE.ps1"
$Report="$Results\AAYS_V20_RERUN_FG444_AUDIT_API_OPEN_$Stamp.txt"
$AuditLog="$Results\FG444_READONLY_AUDIT_V20_$Stamp.log.txt"
$AuditErr="$Results\FG444_READONLY_AUDIT_V20_$Stamp.err.txt"
$PushWork="C:\aays_v20_push_$Stamp"
New-Item -ItemType Directory -Force -Path $Results,$AuditDir | Out-Null
$Port8010=Test-NetConnection -ComputerName localhost -Port 8010 -InformationLevel Quiet
$Port55460=Test-NetConnection -ComputerName localhost -Port 55460 -InformationLevel Quiet
$Probe=""
foreach($u in @("http://localhost:8010/health","http://localhost:8010/docs","http://localhost:8010/openapi.json")){
  try{$r=Invoke-WebRequest -UseBasicParsing -Uri $u -TimeoutSec 12; $Probe += "URL=$u STATUS=$($r.StatusCode) LEN=$($r.Content.Length)`n"}
  catch{$Probe += "URL=$u ERROR=$($_.Exception.Message)`n"}
}
$AuditExit="NOT_RUN"
if((Test-Path $SafeAudit) -and $Port8010 -and $Port55460){
  powershell -NoProfile -ExecutionPolicy Bypass -File $SafeAudit -ProjectRoot "$AaysRepo\terrayield_land_intelligence" -StorageRoot "$StorageRoot" 1> $AuditLog 2> $AuditErr
  $AuditExit=$LASTEXITCODE
}else{
  "SKIPPED_SAFE_AUDIT SafeAuditExists=$(Test-Path $SafeAudit) Port8010=$Port8010 Port55460=$Port55460" | Set-Content -Encoding UTF8 $AuditErr
}
$LatestJson=Get-ChildItem $AuditDir -Filter "FG444_READONLY_AUDIT_*.json" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
$JsonSummary="NO_JSON_FOUND"
$HealthOk=$false
if($LatestJson){
  $Raw=Get-Content $LatestJson.FullName -Raw
  $JsonSummary=$Raw.Substring(0,[Math]::Min(8000,$Raw.Length))
  try{$J=$Raw|ConvertFrom-Json; $HealthOk=[bool]$J.health_http_ok}catch{}
}
$Progress=if($LatestJson -and $HealthOk){80}elseif($LatestJson){76}else{75}
$State=if($LatestJson -and $HealthOk){"fg444_audit_api_health_ok_v20"}elseif($LatestJson){"fg444_audit_json_created_api_health_pending_v20"}else{"fg444_audit_no_json_v20"}
@"
PAGE_KEY=AAYS_SAME_PROJECT_NEW_PAGE
PROJECT=AAYS_TerraYield
TASK=AAYS_V20_RERUN_FG444_AUDIT_API_OPEN
STATUS=$State
SUGGESTED_PROGRESS_PERCENT=$Progress
UPDATED_AT=$(Get-Date -Format s)
PORT_8010=$Port8010
PORT_55460=$Port55460
HTTP_PROBE:
$Probe
AUDIT_EXIT=$AuditExit
AUDIT_JSON=$($LatestJson.FullName)
AUDIT_LOG=$AuditLog
AUDIT_ERR=$AuditErr
AUDIT_LOG_CONTENT:
$(if(Test-Path $AuditLog){Get-Content $AuditLog -Raw}else{"NO_LOG"})
AUDIT_ERR_CONTENT:
$(if(Test-Path $AuditErr){Get-Content $AuditErr -Raw}else{"NO_ERR"})
AUDIT_JSON_SUMMARY:
$JsonSummary
SAFETY:
DB_WRITE=false
PRODUCTION_DEPLOY=false
MIGRATION_DDL=false
FAKE_DATA=false
DESTRUCTIVE_GIT=false
GIT_RESET_HARD=false
GIT_CLEAN=false
FORCE_PUSH=false
MANUAL_OUTPUT_PASTE_REQUIRED=false
"@ | Set-Content -Encoding UTF8 $Report
Remove-Item $PushWork -Recurse -Force -ErrorAction SilentlyContinue
git clone --filter=blob:none --sparse $RepoUrl $PushWork
if(Test-Path $PushWork){
  Push-Location $PushWork
  git config core.longpaths true
  git sparse-checkout set docs/chatgpt_status
  git checkout main
  git pull --ff-only origin main
  New-Item -ItemType Directory -Force -Path "docs\chatgpt_status" | Out-Null
  Copy-Item $Report "docs\chatgpt_status\AAYS_SAME_PROJECT_NEW_PAGE_v20_rerun_fg444_audit_api_open_$Stamp.txt" -Force
  @"
PAGE_KEY: AAYS_SAME_PROJECT_NEW_PAGE
PROJECT: AAYS_TerraYield
STATUS: $State
SUGGESTED_PROGRESS_PERCENT: $Progress
UPDATED_AT: $(Get-Date -Format s)
REPORT_FILE: docs/chatgpt_status/AAYS_SAME_PROJECT_NEW_PAGE_v20_rerun_fg444_audit_api_open_$Stamp.txt
PORT_8010=$Port8010
PORT_55460=$Port55460
AUDIT_EXIT=$AuditExit
AUDIT_JSON=$($LatestJson.FullName)
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
  git add docs/chatgpt_status/AAYS_SAME_PROJECT_NEW_PAGE_v20_rerun_fg444_audit_api_open_$Stamp.txt docs/chatgpt_status/AAYS_SAME_PROJECT_NEW_PAGE_latest_result.txt docs/chatgpt_status/AAYS_SAME_PROJECT_NEW_PAGE_BOOK_OUTPUT.txt
  git commit -m "Add AAYS V20 FG444 audit rerun report"
  git push origin main
  Pop-Location
}
exit 0
'@
$Inner | Set-Content -Encoding UTF8 $Script
$Task=[ordered]@{page_key="AAYS_SAME_PROJECT_NEW_PAGE";project_name="AAYS_TerraYield";id=$TaskId;task_id=$TaskId;script_path=$Script;timeout_seconds=2400;db_write=$false;production_deploy=$false;migration_ddl=$false;fake_data=$false;destructive_git=$false;purpose="rerun FG444 readonly audit while API is open and push GitHub report"}
$Task | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 "$Pending\$TaskId.task.json"
$RunnerActive=@(Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match "portable_queue_runner.ps1" }).Count
if($RunnerActive -eq 0 -and (Test-Path $Runner)){Start-Process powershell -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$Runner`""}
"QUEUED=$TaskId"
"RUNNER_ACTIVE_COUNT=$RunnerActive"
"MANUAL_OUTPUT_PASTE_REQUIRED=false"
