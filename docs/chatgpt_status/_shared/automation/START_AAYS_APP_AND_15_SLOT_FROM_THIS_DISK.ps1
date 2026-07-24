[CmdletBinding()]
param([switch]$NoBrowser, [switch]$NoPanel)

$ErrorActionPreference = "Stop"
$root = [System.IO.Path]::GetFullPath($PSScriptRoot).TrimEnd("\")
$app = Join-Path $root "START_TERRAYIELD_PORTABLE_8012.ps1"
$runner = Join-Path $root "RUN_AAYS_ADAPTIVE_21_SLOT.ps1"
$panel = Join-Path $root "AAYS_PORTABLE_CONTROL_PANEL.cmd"
$state = Join-Path $root "state"
$proof = Join-Path $state "one_click_app_and_21_slot_latest.json"
New-Item -ItemType Directory -Force -Path $state | Out-Null

$result = [ordered]@{
  status = "BLOCKED"
  portable_root = $root
  app_health = $false
  runner_status = "not_started"
  started_at = [DateTime]::UtcNow.ToString("o")
  final_ready = $false
}
try {
  foreach ($required in @($app, $runner, $panel)) {
    if (-not (Test-Path -LiteralPath $required -PathType Leaf)) { throw "REQUIRED_FILE_MISSING: $required" }
  }
  $appArgs = ('-NoProfile -ExecutionPolicy Bypass -File "{0}" -NoBrowser' -f $app)
  $appHelper = Start-Process -FilePath "powershell.exe" -ArgumentList $appArgs -WorkingDirectory $root -WindowStyle Hidden -PassThru
  $appDeadline = (Get-Date).AddSeconds(150)
  $health = $null
  do {
    try {
      $health = Invoke-RestMethod -Uri "http://127.0.0.1:8012/health" -TimeoutSec 4
      if ($health.status -eq "ok" -and $health.app -eq "TerraYield Land Intelligence") { break }
    } catch { }
    if ($appHelper.HasExited -and $appHelper.ExitCode -ne 0) { throw "APP_START_FAILED_$($appHelper.ExitCode)" }
    Start-Sleep -Seconds 2
  } while ((Get-Date) -lt $appDeadline)
  if ($null -eq $health -or $health.status -ne "ok" -or $health.app -ne "TerraYield Land Intelligence") { throw "APP_HEALTH_TIMEOUT" }
  if (-not $appHelper.HasExited) { Stop-Process -Id $appHelper.Id -Force -ErrorAction SilentlyContinue }
  $result.app_health = $true
  $runnerOutput = & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $runner -Action Start
  if ($LASTEXITCODE -ne 0) { throw "RUNNER_START_FAILED_$LASTEXITCODE" }
  $runnerJson = $runnerOutput | Out-String | ConvertFrom-Json
  $result.runner_status = $runnerJson.status
  $result.runner_pid = $runnerJson.pid
  $result.status = "PASS"
  if (-not $NoBrowser) { Start-Process "http://127.0.0.1:8012/england_map_web/index.html" | Out-Null }
  if (-not $NoPanel) { Start-Process -FilePath "cmd.exe" -ArgumentList ('/c "{0}"' -f $panel) -WorkingDirectory $root | Out-Null }
} catch {
  $result.error = $_.Exception.Message
} finally {
  $result.completed_at = [DateTime]::UtcNow.ToString("o")
  [IO.File]::WriteAllText($proof, ($result | ConvertTo-Json -Depth 8) + "`n", (New-Object Text.UTF8Encoding($false)))
}
$result | ConvertTo-Json -Depth 8
if ($result.status -ne "PASS") { exit 1 }
