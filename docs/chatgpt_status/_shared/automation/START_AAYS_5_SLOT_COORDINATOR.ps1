[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$portableRoot = [System.IO.Path]::GetFullPath($PSScriptRoot).TrimEnd("\")
$repoRoot = Join-Path $portableRoot "runner_system\AAYS_WT\AAYS_RUNNER_HEALTHY_20260707"
$initializer = Join-Path $repoRoot "docs\chatgpt_status\_shared\automation\INITIALIZE_AAYS_5_SLOT_COORDINATOR_20260716.ps1"
$runtimeStatus = Join-Path $portableRoot "logs\five_slot_coordinator_latest.json"
$logPath = Join-Path $portableRoot "logs\five_slot_coordinator_bootstrap.log"

if (-not (Test-Path -LiteralPath $repoRoot -PathType Container)) { throw "RUNNER_REPO_MISSING: $repoRoot" }
if (-not (Test-Path -LiteralPath $initializer -PathType Leaf)) { throw "FIVE_SLOT_INITIALIZER_MISSING: $initializer" }
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $runtimeStatus) | Out-Null

$line = "{0} START repo={1}" -f (Get-Date).ToUniversalTime().ToString("o"), $repoRoot
[System.IO.File]::AppendAllText($logPath, $line + [Environment]::NewLine, (New-Object System.Text.UTF8Encoding($false)))
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $initializer -RepoRoot $repoRoot -RuntimeStatusPath $runtimeStatus
if ($LASTEXITCODE -ne 0) { throw "FIVE_SLOT_INITIALIZER_FAILED: exit=$LASTEXITCODE" }

$result = Get-Content -LiteralPath $runtimeStatus -Raw | ConvertFrom-Json
if ($result.status -ne "READY" -or $result.slot_count -ne 5 -or $result.local_runner_concurrency -ne 1) {
  throw "FIVE_SLOT_RUNTIME_VALIDATION_FAILED"
}
$result | ConvertTo-Json -Depth 10
