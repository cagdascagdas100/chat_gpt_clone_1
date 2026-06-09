$ErrorActionPreference = 'Continue'
$Repo = 'cagdascagdas100/chat_gpt_clone_1'
$PageKey = 'FG444_LONDON_ONLY_F_DRIVE'
$Bridge = 'C:\AAYS_GITHUB_BRIDGE_CLEAN2'
$Pending = Join-Path $Bridge 'ai-queue\pending'
$Running = Join-Path $Bridge 'ai-queue\running'
$Scripts = Join-Path $Bridge 'ai-task-scripts'
$State = Join-Path $Bridge 'fg444-controller-state'
$WorkRoot = 'C:\AAYS_GITHUB_BRIDGE_CLEAN2\fg444-london-queue-telemetry-work'
$ReportRel = 'docs/chatgpt_status/FG444_LONDON_FAST_UNBLOCK'
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$Branch = 'fg444-london-queue-telemetry-latest'
New-Item -ItemType Directory -Force $WorkRoot | Out-Null
$RepoDir = Join-Path $WorkRoot 'repo'
if (!(Test-Path $RepoDir)) { git clone "https://github.com/$Repo.git" $RepoDir | Out-Null }
Set-Location $RepoDir
git fetch origin main | Out-Null
git checkout -B $Branch origin/main | Out-Null
$ReportDir = Join-Path $RepoDir $ReportRel
New-Item -ItemType Directory -Force $ReportDir | Out-Null
$ReportPath = Join-Path $ReportDir 'FG444_LONDON_QUEUE_TELEMETRY_LATEST.txt'
$PendingFiles = Get-ChildItem $Pending -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 80 Name, LastWriteTime, Length | Out-String
$RunningFiles = Get-ChildItem $Running -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 80 Name, LastWriteTime, Length | Out-String
$ScriptFiles = Get-ChildItem $Scripts -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 80 Name, LastWriteTime, Length | Out-String
$WatcherFiles = Get-ChildItem $State -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 20 Name, LastWriteTime, Length | Out-String
@"
FG444_LONDON_QUEUE_TELEMETRY_LATEST
UPDATED_AT=$(Get-Date -Format o)
PAGE_KEY=$PageKey
BRIDGE=$Bridge
BRIDGE_EXISTS=$(Test-Path $Bridge)
PENDING_DIR=$Pending
PENDING_EXISTS=$(Test-Path $Pending)
RUNNING_DIR=$Running
RUNNING_EXISTS=$(Test-Path $Running)
SCRIPT_DIR=$Scripts
SCRIPT_DIR_EXISTS=$(Test-Path $Scripts)
STATE_DIR=$State
STATE_DIR_EXISTS=$(Test-Path $State)
F_DRIVE_EXISTS=$(Test-Path F:\)
PENDING_FILES:
$PendingFiles
RUNNING_FILES:
$RunningFiles
TASK_SCRIPTS:
$ScriptFiles
WATCHER_LOGS:
$WatcherFiles
MANUAL_OUTPUT_PASTE_REQUIRED=false
DB_WRITE=false
PRODUCTION_DEPLOY=false
MIGRATION_DDL=false
FAKE_DATA=false
"@ | Set-Content -Encoding UTF8 $ReportPath
git add $ReportRel
git commit -m 'Add FG444 London queue telemetry report' | Out-Null
git push origin $Branch --force | Out-Null
