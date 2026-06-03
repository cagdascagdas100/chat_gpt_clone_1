$Bridge="C:\AAYS_GITHUB_BRIDGE_CLEAN2"
$TaskId="aays-v15-readonly-probe-report"
$ScriptDir="$Bridge\ai-task-scripts"
$Pending="$Bridge\ai-queue\pending"
$Runner="$ScriptDir\portable_queue_runner.ps1"
$Script="$ScriptDir\aays_v15_readonly_probe_report.ps1"
New-Item -ItemType Directory -Force -Path $ScriptDir,$Pending,"$Bridge\ai-results" | Out-Null
$Inner=@'
$ErrorActionPreference="Continue"
$Bridge="C:\AAYS_GITHUB_BRIDGE_CLEAN2"
$RepoUrl="https://github.com/cagdascagdas100/chat_gpt_clone_1.git"
$Stamp=Get-Date -Format "yyyyMMdd_HHmmss"
$Results="$Bridge\ai-results"
$AuditDir="$Bridge\fg444_storage\future_growth\audit"
$Report="$Results\AAYS_V15_READONLY_PROBE_$Stamp.txt"
$PushWork="C:\aays_v15_push_$Stamp"
New-Item -ItemType Directory -Force -Path $Results,$AuditDir | Out-Null
function Add-Step($Step,$Status,$Text){ @"
[$(Get-Date -Format s)] STEP=$Step STATUS=$Status
$Text

"@ | Add-Content -Encoding UTF8 $Report }
@"
PAGE_KEY=AAYS_SAME_PROJECT_NEW_PAGE
PROJECT=AAYS_TerraYield
TASK=AAYS_V15_READONLY_PROBE
STARTED_AT=$(Get-Date -Format s)
MANUAL_OUTPUT_PASTE_REQUIRED=false
SAFETY_DB_WRITE=false
SAFETY_PRODUCTION_DEPLOY=false
SAFETY_MIGRATION_DDL=false
SAFETY_FAKE_DATA=false
SAFETY_DESTRUCTIVE_GIT=false

"@ | Set-Content -Encoding UTF8 $Report
$LatestAudit=Get-ChildItem $AuditDir -Filter "FG444_READONLY_AUDIT_*.json" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
Add-Step "01_latest_audit" "OK" "LATEST_AUDIT=$($LatestAudit.FullName)`n$(if($LatestAudit){Get-Content $LatestAudit.FullName -Raw}else{'NO_AUDIT_JSON'})"
$Port55460=Test-NetConnection -ComputerName localhost -Port 55460 -InformationLevel Quiet
$Port8010=Test-NetConnection -ComputerName localhost -Port 8010 -InformationLevel Quiet
Add-Step "02_ports" "OK" "PORT_55460=$Port55460`nPORT_8010=$Port8010"
$DockerPs=docker ps -a 2>&1 | Out-String
Add-Step "03_docker_ps" "OK" $DockerPs
$ApiLogs=docker logs --tail 200 terrayield_land_api 2>&1 | Out-String
Add-Step "04_api_logs" "OK" $ApiLogs
$DbLogs=docker logs --tail 120 terrayield_land_postgis 2>&1 | Out-String
Add-Step "05_db_logs" "OK" $DbLogs
$Progress=65
$State="fg444_v15_readonly_probe_completed"
Add-Step "06_final" "OK" "STATUS=$State`nSUGGESTED_PROGRESS_PERCENT=$Progress`nPORT_55460=$Port55460`nPORT_8010=$Port8010"
Remove-Item $PushWork -Recurse -Force -ErrorAction SilentlyContinue
git clone --filter=blob:none --sparse $RepoUrl $PushWork
if(Test-Path $PushWork){
  Push-Location $PushWork
  git config core.longpaths true
  git sparse-checkout set docs/chatgpt_status
  git checkout main
  git pull --ff-only origin main
  New-Item -ItemType Directory -Force -Path "docs\chatgpt_status" | Out-Null
  Copy-Item $Report "docs\chatgpt_status\AAYS_SAME_PROJECT_NEW_PAGE_v15_readonly_probe_$Stamp.txt" -Force
  @"
PAGE_KEY: AAYS_SAME_PROJECT_NEW_PAGE
PROJECT: AAYS_TerraYield
STATUS: $State
SUGGESTED_PROGRESS_PERCENT: $Progress
UPDATED_AT: $(Get-Date -Format s)
REPORT_FILE: docs/chatgpt_status/AAYS_SAME_PROJECT_NEW_PAGE_v15_readonly_probe_$Stamp.txt
PORT_55460=$Port55460
PORT_8010=$Port8010
LATEST_AUDIT=$($LatestAudit.FullName)
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
  $Unsafe=@(git status --short | Where-Object { $_ -notmatch "docs/chatgpt_status/" })
  if($Unsafe.Count -eq 0){
    git config user.email "aays-runner@example.local"
    git config user.name "AAYS Runner"
    git add docs/chatgpt_status/AAYS_SAME_PROJECT_NEW_PAGE_v15_readonly_probe_$Stamp.txt docs/chatgpt_status/AAYS_SAME_PROJECT_NEW_PAGE_latest_result.txt docs/chatgpt_status/AAYS_SAME_PROJECT_NEW_PAGE_BOOK_OUTPUT.txt
    git commit -m "Add AAYS V15 readonly probe report"
    git push origin main
  }
  Pop-Location
}
exit 0
'@
$Inner | Set-Content -Encoding UTF8 $Script
$Task=[ordered]@{page_key="AAYS_SAME_PROJECT_NEW_PAGE";project_name="AAYS_TerraYield";id=$TaskId;task_id=$TaskId;script_path=$Script;timeout_seconds=1800;db_write=$false;production_deploy=$false;migration_ddl=$false;fake_data=$false;destructive_git=$false;purpose="collect latest audit and container logs read-only"}
$Task | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 "$Pending\$TaskId.task.json"
$RunnerActive=@(Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match "portable_queue_runner.ps1" }).Count
if($RunnerActive -eq 0 -and (Test-Path $Runner)){Start-Process powershell -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$Runner`""}
"QUEUED=$TaskId"
"RUNNER_ACTIVE_COUNT=$RunnerActive"
"MANUAL_OUTPUT_PASTE_REQUIRED=false"
