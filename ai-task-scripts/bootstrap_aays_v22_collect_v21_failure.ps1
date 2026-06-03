$Bridge="C:\AAYS_GITHUB_BRIDGE_CLEAN2"
$RepoUrl="https://github.com/cagdascagdas100/chat_gpt_clone_1.git"
$Stamp=Get-Date -Format "yyyyMMdd_HHmmss"
$Results="$Bridge\ai-results"
$Queue="$Bridge\ai-queue"
$PushRoot="F:\chatgpt\AAYS_TEMP"
if(-not (Test-Path "F:\")){$PushRoot="C:\"}
$PushWork=Join-Path $PushRoot "aays_v22_collect_v21_failure_$Stamp"
$Report="$Results\AAYS_V22_COLLECT_V21_FAILURE_$Stamp.txt"
New-Item -ItemType Directory -Force -Path $Results,$PushRoot | Out-Null
$FailedTask=Get-ChildItem "$Queue\failed" -File -Filter "aays-v21-candidate-score-readonly-diagnosis*" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
$DoneTask=Get-ChildItem "$Queue\done" -File -Filter "aays-v21-candidate-score-readonly-diagnosis*" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
$PendingTask=Get-ChildItem "$Queue\pending" -File -Filter "aays-v21-candidate-score-readonly-diagnosis*" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
$RunningTask=Get-ChildItem "$Queue\running" -File -Filter "aays-v21-candidate-score-readonly-diagnosis*" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
$RunnerActive=@(Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match "portable_queue_runner.ps1" }).Count
$V21Scripts=Get-ChildItem "$Bridge\ai-task-scripts" -File -Filter "*v21*" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending
$V21Results=Get-ChildItem $Results -File -Filter "*V21*" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 20
$RecentResults=Get-ChildItem $Results -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 40
@"
PAGE_KEY=AAYS_SAME_PROJECT_NEW_PAGE
PROJECT=AAYS_TerraYield
TASK=AAYS_V22_COLLECT_V21_FAILURE
STATUS=v21_failure_collected_v22
SUGGESTED_PROGRESS_PERCENT=80
UPDATED_AT=$(Get-Date -Format s)
RUNNER_ACTIVE_COUNT=$RunnerActive
FAILED_TASK=$($FailedTask.FullName)
DONE_TASK=$($DoneTask.FullName)
PENDING_TASK=$($PendingTask.FullName)
RUNNING_TASK=$($RunningTask.FullName)
MANUAL_OUTPUT_PASTE_REQUIRED=false

FAILED_TASK_CONTENT:
$(if($FailedTask){Get-Content $FailedTask.FullName -Raw}else{"NO_FAILED_TASK"})

DONE_TASK_CONTENT:
$(if($DoneTask){Get-Content $DoneTask.FullName -Raw}else{"NO_DONE_TASK"})

PENDING_TASK_CONTENT:
$(if($PendingTask){Get-Content $PendingTask.FullName -Raw}else{"NO_PENDING_TASK"})

RUNNING_TASK_CONTENT:
$(if($RunningTask){Get-Content $RunningTask.FullName -Raw}else{"NO_RUNNING_TASK"})

V21_SCRIPTS:
$($V21Scripts | ForEach-Object { "$($_.LastWriteTime.ToString('s')) $($_.FullName)" } | Out-String)

V21_RESULTS:
$($V21Results | ForEach-Object { "$($_.LastWriteTime.ToString('s')) $($_.Length) $($_.FullName)" } | Out-String)

RECENT_RESULTS:
$($RecentResults | ForEach-Object { "$($_.LastWriteTime.ToString('s')) $($_.Length) $($_.FullName)" } | Out-String)

SAFETY:
DB_WRITE=false
PRODUCTION_DEPLOY=false
MIGRATION_DDL=false
FAKE_DATA=false
DESTRUCTIVE_GIT=false
GIT_RESET_HARD=false
GIT_CLEAN=false
FORCE_PUSH=false
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
  Copy-Item $Report "docs\chatgpt_status\AAYS_SAME_PROJECT_NEW_PAGE_v22_collect_v21_failure_$Stamp.txt" -Force
@"
PAGE_KEY: AAYS_SAME_PROJECT_NEW_PAGE
PROJECT: AAYS_TerraYield
STATUS: v21_failure_collected_v22
SUGGESTED_PROGRESS_PERCENT: 80
UPDATED_AT: $(Get-Date -Format s)
REPORT_FILE: docs/chatgpt_status/AAYS_SAME_PROJECT_NEW_PAGE_v22_collect_v21_failure_$Stamp.txt
RUNNER_ACTIVE_COUNT=$RunnerActive
FAILED_TASK=$($FailedTask.FullName)
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
  git add docs/chatgpt_status/AAYS_SAME_PROJECT_NEW_PAGE_v22_collect_v21_failure_$Stamp.txt docs/chatgpt_status/AAYS_SAME_PROJECT_NEW_PAGE_latest_result.txt docs/chatgpt_status/AAYS_SAME_PROJECT_NEW_PAGE_BOOK_OUTPUT.txt
  git commit -m "Add AAYS V22 V21 failure collection report"
  git push origin main
  Pop-Location
}
"V22_FAILURE_REPORT_WRITTEN=$Report"
"RUNNER_ACTIVE_COUNT=$RunnerActive"
"MANUAL_OUTPUT_PASTE_REQUIRED=false"
