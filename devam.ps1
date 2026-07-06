$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$launcher = Join-Path $repoRoot "docs/chatgpt_status/_shared/automation/START_AAYS_SINGLE_RUNNER_WITH_PANEL_20260706.ps1"
if (-not (Test-Path -LiteralPath $launcher)) {
  throw "Missing shared runner launcher: $launcher"
}
& powershell -NoProfile -ExecutionPolicy Bypass -File $launcher
