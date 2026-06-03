$Bridge="C:\AAYS_GITHUB_BRIDGE_CLEAN2"
$RepoUrl="https://github.com/cagdascagdas100/chat_gpt_clone_1.git"
$Stamp=Get-Date -Format "yyyyMMdd_HHmmss"
$Results="$Bridge\ai-results"
$Queue="$Bridge\ai-queue"
$Runner="$Bridge\ai-task-scripts\portable_queue_runner.ps1"
$Report="$Results\AAYS_V21_QUEUE_STATUS_$Stamp.txt"
$PushRoot="F:\chatgpt\AAYS_TEMP"
if(-not (Test-Path "F:\")){$PushRoot="C:\"}
$PushWork=Join-Path $PushRoot "aays_v21_queue_status_push_$Stamp"
New-Item -ItemType Directory -Force -Path $Results,$PushRoot | Out-Null
$RunnerActive=@(Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match "portable_queue_runner.ps1" }).Count
$Pending=Get-ChildItem "$Queue\pending" -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 30
$Running=Get-ChildItem "$Queue\running" -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 30
$Done=Get-ChildItem "$Queue\done" -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 30
$Failed=Get-ChildItem "$Queue\failed" -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 30
$V21Local=Get-ChildItem $Results -Filter "AAYS_V21_CANDIDATE_SCORE_READONLY_DIAGNOSIS_*.txt" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
@"
PAGE_KEY=AAYS_SAME_PROJECT_NEW_PAGE
PROJECT=AAYS_TerraYield
TASK=AAYS_V21_QUEUE_STATUS_REPORT
STATUS=v21_queue_status_checked
SUGGESTED_PROGRESS_PERCENT=80
UPDATED_AT=$(Get-Date -Format s)
RUNNER_ACTIVE_COUNT=$RunnerActive
RUNNER_PATH=$Runner
V21_LOCAL_REPORT=$($V21Local.FullName)
MANUAL_OUTPUT_PASTE_REQUIRED=false

PENDING_FILES:
$($Pending | ForEach-Object { "$($_.LastWriteTime.ToString('s')) $($_.FullName)" } | Out-String)

RUNNING_FILES:
$($Running | ForEach-Object { "$($_.LastWriteTime.ToString('s')) $($_.FullName)" } | Out-String)

DONE_FILES:
$($Done | ForEach-Object { "$($_.LastWriteTime.ToString('s')) $($_.FullName)" } | Out-String)

FAILED_FILES:
$($Failed | ForEach-Object { "$($_.LastWriteTime.ToString('s')) $($_.FullName)" } | Out-String)

V21_LOCAL_REPORT_CONTENT:
$(if($V21Local){Get-Content $V21Local.FullName -Raw}else{"NO_V21_LOCAL_REPORT_FOUND"})

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
  Copy-Item $Report "docs\chatgpt_status\AAYS_SAME_PROJECT_NEW_PAGE_v21_queue_status_$Stamp.txt" -Force
@"
PAGE_KEY: AAYS_SAME_PROJECT_NEW_PAGE
PROJECT: AAYS_TerraYield
STATUS: v21_queue_status_checked
SUGGESTED_PROGRESS_PERCENT: 80
UPDATED_AT: $(Get-Date -Format s)
REPORT_FILE: docs/chatgpt_status/AAYS_SAME_PROJECT_NEW_PAGE_v21_queue_status_$Stamp.txt
RUNNER_ACTIVE_COUNT=$RunnerActive
V21_LOCAL_REPORT=$($V21Local.FullName)
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
  git add docs/chatgpt_status/AAYS_SAME_PROJECT_NEW_PAGE_v21_queue_status_$Stamp.txt docs/chatgpt_status/AAYS_SAME_PROJECT_NEW_PAGE_latest_result.txt docs/chatgpt_status/AAYS_SAME_PROJECT_NEW_PAGE_BOOK_OUTPUT.txt
  git commit -m "Add AAYS V21 queue status report"
  git push origin main
  Pop-Location
}
"QUEUE_STATUS_REPORT_WRITTEN=$Report"
"RUNNER_ACTIVE_COUNT=$RunnerActive"
"MANUAL_OUTPUT_PASTE_REQUIRED=false"
