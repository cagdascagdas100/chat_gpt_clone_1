$Bridge="C:\AAYS_GITHUB_BRIDGE_CLEAN2"
$TaskId="aays-v14-retry-fg444-readonly-audit-report"
$ScriptDir="$Bridge\ai-task-scripts"
$Pending="$Bridge\ai-queue\pending"
$Runner="$ScriptDir\portable_queue_runner.ps1"
$Script="$ScriptDir\aays_v14_retry_fg444_readonly_audit_report.ps1"
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
$Report="$Results\AAYS_V14_RETRY_AUDIT_$Stamp.txt"
$PushWork="C:\aays_v14_push_$Stamp"
New-Item -ItemType Directory -Force -Path $Results,$AuditDir | Out-Null
function Add-Step($Step,$Status,$Text){ @"
[$(Get-Date -Format s)] STEP=$Step STATUS=$Status
$Text

"@ | Add-Content -Encoding UTF8 $Report }
@"
PAGE_KEY=AAYS_SAME_PROJECT_NEW_PAGE
PROJECT=AAYS_TerraYield
TASK=AAYS_V14_RETRY_FG444_READONLY_AUDIT
STARTED_AT=$(Get-Date -Format s)
SAFETY_DB_WRITE=false
SAFETY_PRODUCTION_DEPLOY=false
SAFETY_MIGRATION_DDL=false
SAFETY_FAKE_DATA=false
SAFETY_DESTRUCTIVE_GIT=false
MANUAL_OUTPUT_PASTE_REQUIRED=false

"@ | Set-Content -Encoding UTF8 $Report
Add-Step "01_port_check" "BEGIN" "Checking DB 55460 and API 8010."
$Port55460=Test-NetConnection -ComputerName localhost -Port 55460 -InformationLevel Quiet
$Port8010=Test-NetConnection -ComputerName localhost -Port 8010 -InformationLevel Quiet
Add-Step "01_port_check" "OK" "PORT_55460=$Port55460`nPORT_8010=$Port8010"
Add-Step "02_docker_ps" "BEGIN" "Listing containers before retry."
$DockerPs=docker ps -a 2>&1 | Out-String
Add-Step "02_docker_ps" "OK" $DockerPs
$Attempts=@()
for($i=1;$i -le 3;$i++){
  if(-not (Test-Path $SafeAudit)){
    $Attempts += "attempt_$i=SAFE_AUDIT_SCRIPT_MISSING"
    Add-Step "03_audit_attempt_$i" "FAIL" "Safe audit script missing: $SafeAudit"
    break
  }
  $Log="$Results\FG444_READONLY_AUDIT_V14_${Stamp}_attempt${i}.log.txt"
  $Err="$Results\FG444_READONLY_AUDIT_V14_${Stamp}_attempt${i}.err.txt"
  Add-Step "03_audit_attempt_$i" "BEGIN" "Running read-only audit attempt $i."
  powershell -NoProfile -ExecutionPolicy Bypass -File $SafeAudit -ProjectRoot "$AaysRepo\terrayield_land_intelligence" -StorageRoot "$StorageRoot" 1> $Log 2> $Err
  $Exit=$LASTEXITCODE
  $LatestJson=Get-ChildItem $AuditDir -Filter "FG444_READONLY_AUDIT_*.json" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
  $Attempts += "attempt_$i exit=$Exit json=$($LatestJson.FullName) log=$Log err=$Err"
  Add-Step "03_audit_attempt_$i" "OK" "EXIT=$Exit`nJSON=$($LatestJson.FullName)`nLOG=$Log`nERR=$Err`nLOG_CONTENT:`n$(if(Test-Path $Log){Get-Content $Log -Raw}else{'NO_LOG'})`nERR_CONTENT:`n$(if(Test-Path $Err){Get-Content $Err -Raw}else{'NO_ERR'})"
  if($LatestJson){ break }
  Start-Sleep -Seconds 20
}
$LatestJson=Get-ChildItem $AuditDir -Filter "FG444_READONLY_AUDIT_*.json" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
$Progress=if($LatestJson){60}else{54}
$State=if($LatestJson){"fg444_readonly_audit_json_created_v14"}else{"fg444_readonly_audit_retry_remote_disconnect_v14"}
Add-Step "04_final_summary" "OK" "STATUS=$State`nSUGGESTED_PROGRESS_PERCENT=$Progress`nLATEST_JSON=$($LatestJson.FullName)`nATTEMPTS=$($Attempts -join ' | ')"
Remove-Item $PushWork -Recurse -Force -ErrorAction SilentlyContinue
git clone --filter=blob:none --sparse $RepoUrl $PushWork
if(Test-Path $PushWork){
  Push-Location $PushWork
  git config core.longpaths true
  git sparse-checkout set docs/chatgpt_status
  git checkout main
  git pull --ff-only origin main
  New-Item -ItemType Directory -Force -Path "docs\chatgpt_status" | Out-Null
  Copy-Item $Report "docs\chatgpt_status\AAYS_SAME_PROJECT_NEW_PAGE_v14_retry_audit_$Stamp.txt" -Force
  @"
PAGE_KEY: AAYS_SAME_PROJECT_NEW_PAGE
PROJECT: AAYS_TerraYield
STATUS: $State
SUGGESTED_PROGRESS_PERCENT: $Progress
UPDATED_AT: $(Get-Date -Format s)
REPORT_FILE: docs/chatgpt_status/AAYS_SAME_PROJECT_NEW_PAGE_v14_retry_audit_$Stamp.txt
LATEST_JSON=$($LatestJson.FullName)
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
    git add docs/chatgpt_status/AAYS_SAME_PROJECT_NEW_PAGE_v14_retry_audit_$Stamp.txt docs/chatgpt_status/AAYS_SAME_PROJECT_NEW_PAGE_latest_result.txt docs/chatgpt_status/AAYS_SAME_PROJECT_NEW_PAGE_BOOK_OUTPUT.txt
    git commit -m "Add AAYS V14 FG444 retry audit report"
    git push origin main
  }
  Pop-Location
}
exit 0
'@
$Inner | Set-Content -Encoding UTF8 $Script
$Task=[ordered]@{page_key="AAYS_SAME_PROJECT_NEW_PAGE";project_name="AAYS_TerraYield";id=$TaskId;task_id=$TaskId;script_path=$Script;timeout_seconds=2400;db_write=$false;production_deploy=$false;migration_ddl=$false;fake_data=$false;destructive_git=$false;purpose="retry FG444 readonly audit up to 3 times and push GitHub status report"}
$Task | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 "$Pending\$TaskId.task.json"
$RunnerActive=@(Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match "portable_queue_runner.ps1" }).Count
if($RunnerActive -eq 0 -and (Test-Path $Runner)){Start-Process powershell -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$Runner`""}
"QUEUED=$TaskId"
"RUNNER_ACTIVE_COUNT=$RunnerActive"
"MANUAL_OUTPUT_PASTE_REQUIRED=false"
