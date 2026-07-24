[CmdletBinding()]
param(
  [string]$RepoRoot = "C:\AAYS_WT\AAYS_REPAIR_20260706_1738",
  [string]$Branch = "codex/aays-single-runner-v5-20260706"
)

$ErrorActionPreference = "Stop"
if (!(Test-Path -LiteralPath $RepoRoot)) { throw "RepoRoot not found: $RepoRoot" }
Set-Location $RepoRoot

& git fetch origin $Branch
if ($LASTEXITCODE -ne 0) { throw "git fetch failed" }
& git checkout $Branch
if ($LASTEXITCODE -ne 0) { throw "git checkout failed" }
& git pull --ff-only origin $Branch
if ($LASTEXITCODE -ne 0) { throw "git pull failed" }

$runner = Join-Path $RepoRoot "docs\chatgpt_status\_shared\automation\RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_V5_20260706.ps1"
if (!(Test-Path -LiteralPath $runner)) { throw "Runner not found: $runner" }

$outDir = Join-Path $RepoRoot "docs\chatgpt_status\_shared\reports"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$outFile = Join-Path $outDir "manual_run_v5_repair_clone_once_$stamp.txt"

& powershell -NoProfile -ExecutionPolicy Bypass -File $runner -RepoRoot $RepoRoot -MaxTasks 1 *>&1 | Tee-Object -FilePath $outFile
$runnerExit = $LASTEXITCODE

& git status --short
& git add --all
& git commit -m "AAYS manual V5 repair clone runner evidence $stamp"
$commitExit = $LASTEXITCODE

& git push origin HEAD:$Branch
$pushExit = $LASTEXITCODE

Write-Output "RUNNER_EXIT=$runnerExit"
Write-Output "COMMIT_EXIT=$commitExit"
Write-Output "PUSH_EXIT=$pushExit"
Write-Output "OUTPUT_FILE=$outFile"

if ($runnerExit -ne 0) { exit $runnerExit }
if ($pushExit -ne 0) { exit $pushExit }
exit 0
