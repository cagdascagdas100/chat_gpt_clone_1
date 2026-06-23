param(
  [string]$RepoRoot = (Get-Location).Path,
  [string]$PageKey = "internet_access_parcel_layer_low_credit_20260612"
)

$ErrorActionPreference = "Stop"
$PageRoot = Join-Path $RepoRoot "docs/chatgpt_status/$PageKey"
$QueueDir = Join-Path $PageRoot "queue"
$StatusDir = Join-Path $PageRoot "status"
$ReportDir = Join-Path $PageRoot "reports"
$RunnerTasksDir = Join-Path $PageRoot "runner_tasks"
$Now = Get-Date -Format "yyyyMMdd-HHmmss"

New-Item -ItemType Directory -Force -Path $StatusDir,$ReportDir,$RunnerTasksDir | Out-Null

$HeartbeatPath = Join-Path $StatusDir "shared-runner-heartbeat-$Now.json"
@{
  page_key = $PageKey
  timestamp = $Now
  repo_root = $RepoRoot
  runner_contract = "single_shared_runner_only"
  new_runner_started = $false
  status = "RUNNER_STARTED_SINGLE_PASS"
} | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 $HeartbeatPath

$QueueFile = Get-ChildItem $QueueDir -Filter "*.json" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (!$QueueFile) { throw "No queue json found under $QueueDir" }

$Queue = Get-Content $QueueFile.FullName -Raw | ConvertFrom-Json
$AutomationRel = $Queue.automation_script
if (!$AutomationRel) { throw "Queue has no automation_script" }

$AutomationPath = Join-Path $RepoRoot $AutomationRel
if (!(Test-Path $AutomationPath)) { throw "Automation script not found: $AutomationPath" }

$ReportPath = Join-Path $ReportDir "shared-runner-output-$Now.md"
@"
# Shared Runner Output

page_key: $PageKey
queue_file: $($QueueFile.FullName)
automation_script: $AutomationPath
started_at: $Now
new_runner_started: false
"@ | Set-Content -Encoding UTF8 $ReportPath

& powershell -NoProfile -ExecutionPolicy Bypass -File $AutomationPath
$ExitCode = $LASTEXITCODE
$Done = Get-Date -Format "yyyyMMdd-HHmmss"

@{
  page_key = $PageKey
  timestamp = $Done
  queue_file = $QueueFile.FullName
  automation_script = $AutomationPath
  automation_exit_code = $ExitCode
  runner_contract = "single_shared_runner_only"
  new_runner_started = $false
  status = "RUNNER_FINISHED_SINGLE_PASS"
} | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 (Join-Path $StatusDir "shared-runner-status-$Done.json")

Add-Content -Encoding UTF8 -Path $ReportPath -Value "`nfinished_at: $Done`nautomation_exit_code: $ExitCode`n"

Set-Location $RepoRoot
git add "docs/chatgpt_status/$PageKey/status" "docs/chatgpt_status/$PageKey/reports" "docs/chatgpt_status/$PageKey/runner_tasks"
$Changes = git status --porcelain
if ($Changes) {
  git commit -m "Write internet access shared runner output"
  git push
}
