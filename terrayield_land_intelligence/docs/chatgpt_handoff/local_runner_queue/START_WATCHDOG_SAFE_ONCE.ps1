$ErrorActionPreference = "Stop"

$Repo = "C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence"
$Branch = "security-accuracy-expansion-20260508"
$Runner = Join-Path $Repo "docs\chatgpt_handoff\local_runner_queue\AAYS_LOCAL_RUNNER_WATCHDOG_SAFE.ps1"
$LogDir = Join-Path $Repo "docs\chatgpt_handoff\local_runner_queue\outputs"
$StartLog = Join-Path $LogDir "WATCHDOG_START_ONCE_LOG.txt"

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

Set-Location $Repo

git fetch origin $Branch | Tee-Object -FilePath $StartLog
git checkout $Branch | Tee-Object -FilePath $StartLog -Append
git pull --ff-only origin $Branch | Tee-Object -FilePath $StartLog -Append

if (!(Test-Path $Runner)) {
  throw "Watchdog runner not found: $Runner"
}

@(
  "timestamp_utc=$([DateTime]::UtcNow.ToString('o'))",
  "action=start_watchdog_safe_once",
  "repo=$Repo",
  "branch=$Branch",
  "runner=$Runner",
  "db_write=none",
  "ddl=none",
  "migration_apply=none",
  "prod_deploy=none",
  "secret_values_printed=false"
) | Add-Content -LiteralPath $StartLog -Encoding UTF8

powershell -ExecutionPolicy Bypass -File $Runner | Tee-Object -FilePath $StartLog -Append

Write-Host "Watchdog safe one-shot run completed. Check WATCHDOG_HEARTBEAT.txt and cloud_ready_20260517 reports."
