$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$launcher = Join-Path $repoRoot "docs/chatgpt_status/_shared/automation/START_AAYS_SINGLE_RUNNER_WITH_PANEL.ps1"
$builder = Join-Path $repoRoot "docs/chatgpt_status/_shared/automation/BUILD_AAYS_PAGE_PANEL_INDEX.ps1"
$panelFile = Join-Path $repoRoot "england_map_web/runner_panel.html"
$panelUrl = "http://127.0.0.1:8010/england_map_web/runner_panel.html"

if (-not (Test-Path -LiteralPath $launcher)) {
  throw "Missing shared runner launcher: $launcher"
}
if (-not (Test-Path -LiteralPath $builder)) {
  throw "Missing panel index builder: $builder"
}

& powershell -NoProfile -ExecutionPolicy Bypass -File $builder -RepoRoot $repoRoot -EnsurePageDirs | Out-Null
& powershell -NoProfile -ExecutionPolicy Bypass -File $launcher -NoPanel | Out-Null

try {
  $response = Invoke-WebRequest -UseBasicParsing -Uri $panelUrl -TimeoutSec 3
  if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500) {
    Start-Process $panelUrl
    exit 0
  }
} catch {
  # Fall back to the local HTML file when the FastAPI static route is not up.
}

if (Test-Path -LiteralPath $panelFile) {
  Start-Process $panelFile
} else {
  throw "Missing runner panel file: $panelFile"
}
