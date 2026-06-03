$Bridge="C:\AAYS_GITHUB_BRIDGE_CLEAN2"
$TaskId="aays-v13-collect-audit-logs-github-report"
$ScriptDir="$Bridge\ai-task-scripts"
$Pending="$Bridge\ai-queue\pending"
$Runner="$ScriptDir\portable_queue_runner.ps1"
$Script="$ScriptDir\aays_v13_collect_audit_logs_github_report.ps1"

New-Item -ItemType Directory -Force -Path $ScriptDir,$Pending,"$Bridge\ai-results" | Out-Null

$Inner = @'
$ErrorActionPreference="Continue"
$Bridge="C:\AAYS_GITHUB_BRIDGE_CLEAN2"
$RepoUrl="https://github.com/cagdascagdas100/chat_gpt_clone_1.git"
$Stamp=Get-Date -Format "yyyyMMdd_HHmmss"
$Results="$Bridge\ai-results"
$AuditDir="$Bridge\fg444_storage\future_growth\audit"
$Report="$Results\AAYS_V13_AUDIT_LOG_COLLECT_$Stamp.txt"
$PushWork="C:\aays_v13_push_$Stamp"
New-Item -ItemType Directory -Force -Path $Results,$AuditDir | Out-Null
$LatestLog=Get-ChildItem $Results -Filter "FG444_READONLY_AUDIT_V12_*.log.txt" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
$LatestErr=Get-ChildItem $Results -Filter "FG444_READONLY_AUDIT_V12_*.err.txt" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
$LatestJson=Get-ChildItem $AuditDir -Filter "FG444_READONLY_AUDIT_*.json" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
$Progress=if($LatestJson){55}else{52}
$State=if($LatestJson){"fg444_audit_json_found_v13"}else{"fg444_audit_logs_collected_json_missing_v13"}
$LogContent=if($LatestLog){Get-Content $LatestLog.FullName -Raw}else{"NO_LOG_FOUND"}
$ErrContent=if($LatestErr){Get-Content $LatestErr.FullName -Raw}else{"NO_ERR_FOUND"}
$JsonContent=if($LatestJson){Get-Content $LatestJson.FullName -Raw}else{"NO_JSON_FOUND"}
@"
PAGE_KEY=AAYS_SAME_PROJECT_NEW_PAGE
PROJECT=AAYS_TerraYield
TASK=AAYS_V13_AUDIT_LOG_COLLECT
STATUS=$State
SUGGESTED_PROGRESS_PERCENT=$Progress
UPDATED_AT=$(Get-Date -Format s)

LATEST_LOG=$($LatestLog.FullName)
LATEST_ERR=$($LatestErr.FullName)
LATEST_JSON=$($LatestJson.FullName)

AUDIT_LOG_CONTENT:
$LogContent

AUDIT_ERR_CONTENT:
$ErrContent

AUDIT_JSON_CONTENT:
$JsonContent

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
  Copy-Item $Report "docs\chatgpt_status\AAYS_SAME_PROJECT_NEW_PAGE_v13_audit_log_collect_$Stamp.txt" -Force
  @"
PAGE_KEY: AAYS_SAME_PROJECT_NEW_PAGE
PROJECT: AAYS_TerraYield
STATUS: $State
SUGGESTED_PROGRESS_PERCENT: $Progress
UPDATED_AT: $(Get-Date -Format s)
REPORT_FILE: docs/chatgpt_status/AAYS_SAME_PROJECT_NEW_PAGE_v13_audit_log_collect_$Stamp.txt
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
  $Unsafe=@(git status --short | Where-Object { $_ -notmatch "docs/chatgpt_status/" })
  if($Unsafe.Count -eq 0){
    git config user.email "aays-runner@example.local"
    git config user.name "AAYS Runner"
    git add docs/chatgpt_status/AAYS_SAME_PROJECT_NEW_PAGE_v13_audit_log_collect_$Stamp.txt docs/chatgpt_status/AAYS_SAME_PROJECT_NEW_PAGE_latest_result.txt docs/chatgpt_status/AAYS_SAME_PROJECT_NEW_PAGE_BOOK_OUTPUT.txt
    git commit -m "Add AAYS V13 audit log report"
    git push origin main
  }
  Pop-Location
}
exit 0
'@

$Inner | Set-Content -Encoding UTF8 $Script
$Task=[ordered]@{page_key="AAYS_SAME_PROJECT_NEW_PAGE";project_name="AAYS_TerraYield";id=$TaskId;task_id=$TaskId;script_path=$Script;timeout_seconds=1800;db_write=$false;production_deploy=$false;migration_ddl=$false;fake_data=$false;destructive_git=$false;purpose="collect V12 FG444 readonly audit logs/json and push GitHub status report"}
$Task | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 "$Pending\$TaskId.task.json"
$RunnerActive=@(Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match "portable_queue_runner.ps1" }).Count
if($RunnerActive -eq 0 -and (Test-Path $Runner)){Start-Process powershell -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$Runner`""}
"QUEUED=$TaskId"
"RUNNER_ACTIVE_COUNT=$RunnerActive"
"MANUAL_OUTPUT_PASTE_REQUIRED=false"
