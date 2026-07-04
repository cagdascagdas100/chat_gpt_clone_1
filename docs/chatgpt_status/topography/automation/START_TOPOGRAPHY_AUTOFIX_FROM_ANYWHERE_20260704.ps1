param(
  [string]$RepoRoot = 'F:\chatgpt\chat_gpt_clone_1_main',
  [string]$RepoUrl = 'https://github.com/cagdascagdas100/chat_gpt_clone_1.git'
)

$ErrorActionPreference = 'Stop'
$logDir = Join-Path $RepoRoot 'docs\chatgpt_status\topography\logs'
$logPath = Join-Path $logDir 'topography_autofix_latest_20260704.log'

function Ensure-Dir([string]$Path) {
  if (-not (Test-Path $Path)) { New-Item -ItemType Directory -Force -Path $Path | Out-Null }
}
function Log([string]$Message) {
  $line = ((Get-Date).ToString('s') + ' ' + $Message)
  Write-Host $line
  if (Test-Path $logDir) { Add-Content -Path $logPath -Value $line -Encoding UTF8 }
}
function Fail([string]$Message) {
  Log ('ERROR ' + $Message)
  throw $Message
}

if (-not (Test-Path 'F:\')) { Fail 'F drive not found. This Topography flow is F-disk only.' }
Ensure-Dir (Split-Path -Parent $RepoRoot)

if (-not (Get-Command git -ErrorAction SilentlyContinue)) { Fail 'git command not found. Install Git for Windows or open a shell where git is available.' }

if (-not (Test-Path $RepoRoot)) {
  Log ('cloning repo to ' + $RepoRoot)
  git clone $RepoUrl $RepoRoot
}

if (-not (Test-Path (Join-Path $RepoRoot '.git'))) { Fail ('RepoRoot exists but is not a git repo: ' + $RepoRoot) }
Ensure-Dir $logDir
Set-Location $RepoRoot
$env:AAYS_REPO_ROOT = $RepoRoot

Log 'git sync start'
$dirty = git status --porcelain
if ($dirty) {
  Log 'local changes detected; stashing before pull'
  git stash push -u -m ('topography-autofix-' + (Get-Date -Format yyyyMMdd_HHmmss)) | Out-Host
}

git fetch origin main | Out-Host
git checkout main | Out-Host
git pull --ff-only origin main | Out-Host

$bridge = Join-Path $RepoRoot 'docs\chatgpt_status\topography\automation\topography_single_runner_bridge_20260703.ps1'
if (-not (Test-Path $bridge)) { Fail ('bridge script missing after pull: ' + $bridge) }

$csv = Join-Path $RepoRoot 'docs\chatgpt_status\topography\fixtures\topography_verified_rows_template_20260703.csv'
if (-not (Test-Path $csv)) {
  Ensure-Dir (Split-Path -Parent $csv)
  'parcel_id,parcel_ref,elevation_sea_level_m,regional_average_elevation_m,elevation_difference_regional_average_m,elevation_class,color_category,confidence_rating,confidence_percent,source,source_url,source_date,matching_method,calculation_explanation,accuracy_score_4,needs_manual_review,changed_in_latest_run' | Set-Content -Path $csv -Encoding UTF8
  Log 'created missing verified rows CSV header only; no fake parcel row added'
}

Log 'running Topography bridge first pass'
powershell -NoProfile -ExecutionPolicy Bypass -File $bridge -RepoRoot $RepoRoot | Tee-Object -FilePath $logPath -Append

$smoke = Join-Path $RepoRoot 'docs\chatgpt_status\topography\automation\topography_browser_smoke_check_20260704.js'
if ((Test-Path $smoke) -and (Get-Command node -ErrorAction SilentlyContinue)) {
  Log 'running browser smoke check'
  try {
    node $smoke | Tee-Object -FilePath $logPath -Append
  } catch {
    Log ('browser smoke failed but bridge will record blocker: ' + $_.Exception.Message)
  }
} else {
  Log 'browser smoke skipped: node or smoke script missing'
}

Log 'running Topography bridge final pass'
powershell -NoProfile -ExecutionPolicy Bypass -File $bridge -RepoRoot $RepoRoot | Tee-Object -FilePath $logPath -Append

$status = Join-Path $RepoRoot 'docs\chatgpt_status\topography\status\topography_current_status_20260703.txt'
if (Test-Path $status) {
  Log 'final status follows'
  Get-Content $status | Out-Host
} else {
  Fail 'status file was not produced'
}

Log 'autofix complete'
