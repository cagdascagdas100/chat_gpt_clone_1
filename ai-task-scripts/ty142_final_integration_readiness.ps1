$ErrorActionPreference = "Stop"

$BridgeRoot = "C:\AAYS1_GITHUB_BRIDGE\chat_gpt_clone_1"
$WorkspaceRoot = "C:\Users\cagda\Documents\GitHub\AAYS"
$BackendRoot = Join-Path $WorkspaceRoot "terrayield_land_intelligence"
$FrontendRoot = Join-Path $WorkspaceRoot "england_map_web"
$ResultsDir = Join-Path $BridgeRoot "ai-results"
$ReportPath = Join-Path $ResultsDir "ty142-final-integration-readiness.report.md"
$ResultPath = Join-Path $ResultsDir "ty142-final-integration-readiness.result.json"

New-Item -ItemType Directory -Force -Path $ResultsDir | Out-Null

function Test-Endpoint {
  param([string]$Url)
  try {
    $Response = Invoke-WebRequest -Uri $Url -TimeoutSec 5 -UseBasicParsing
    return [ordered]@{ url = $Url; reachable = $true; status_code = [int]$Response.StatusCode }
  } catch {
    return [ordered]@{ url = $Url; reachable = $false; status_code = 0 }
  }
}

function Test-PathFlag {
  param([string]$Path)
  return [ordered]@{ path = $Path; exists = (Test-Path -Path $Path) }
}

function Count-MatchesSafe {
  param([string]$Root, [string[]]$Patterns)
  if (-not (Test-Path -Path $Root)) { return 0 }
  $count = 0
  $files = Get-ChildItem -Path $Root -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -notmatch "\\(node_modules|\.git|\.venv|venv|__pycache__|dist|build)\\" -and $_.Length -lt 1048576 }
  foreach ($file in $files) {
    try {
      $text = Get-Content -Path $file.FullName -Raw -ErrorAction Stop
      foreach ($pattern in $Patterns) {
        if ($text -match $pattern) { $count++ }
      }
    } catch {}
  }
  return $count
}

$Paths = [ordered]@{
  workspace_root = Test-PathFlag $WorkspaceRoot
  backend_root = Test-PathFlag $BackendRoot
  frontend_root = Test-PathFlag $FrontendRoot
  bridge_root = Test-PathFlag $BridgeRoot
  backend_config = Test-PathFlag (Join-Path $BackendRoot "app\core\config.py")
  backend_tests = Test-PathFlag (Join-Path $BackendRoot "tests")
  frontend_package = Test-PathFlag (Join-Path $FrontendRoot "package.json")
}

$Endpoints = @(
  Test-Endpoint "http://127.0.0.1:8010/health",
  Test-Endpoint "http://localhost:8000/health",
  Test-Endpoint "http://localhost:3000"
)

$RiskScan = [ordered]@{
  backend_fake_demo_todo_matches = Count-MatchesSafe $BackendRoot @("fake", "hardcoded", "TODO", "FIXME")
  frontend_fake_demo_todo_matches = Count-MatchesSafe $FrontendRoot @("fake", "hardcoded", "TODO", "FIXME")
}

$Readiness = [ordered]@{
  backend_path_ready = $Paths.backend_root.exists
  frontend_path_ready = $Paths.frontend_root.exists
  config_present = $Paths.backend_config.exists
  backend_tests_present = $Paths.backend_tests.exists
  frontend_package_present = $Paths.frontend_package.exists
  any_endpoint_reachable = [bool](($Endpoints | Where-Object { $_.reachable }).Count -gt 0)
  secrets_values_logged = $false
  product_validation_complete = $false
}

$Missing = @()
if (-not $Readiness.backend_path_ready) { $Missing += "backend root missing" }
if (-not $Readiness.frontend_path_ready) { $Missing += "frontend root missing" }
if (-not $Readiness.config_present) { $Missing += "backend config not found" }
if (-not $Readiness.backend_tests_present) { $Missing += "backend tests folder not found" }
if (-not $Readiness.frontend_package_present) { $Missing += "frontend package.json not found" }
if (-not $Readiness.any_endpoint_reachable) { $Missing += "no local endpoint reachable; start backend/frontend for live smoke test" }
$Missing += "manual browser UI acceptance still required"
$Missing += "production deployment evidence still required"

$Status = if ($Missing.Count -le 2) { "completed_with_minor_gaps" } else { "completed_with_required_followup" }

$Audit = [ordered]@{
  task_id = "ty142-final-integration-readiness"
  status = $Status
  generated_at = (Get-Date).ToString("s")
  paths = $Paths
  endpoints = $Endpoints
  risk_scan = $RiskScan
  readiness = $Readiness
  missing_items = $Missing
  policy = [ordered]@{
    no_secret_values_logged = $true
    fake_data_allowed_in_production = $false
    evidence_required_for_scores = $true
    source_url_required_for_high_confidence = $true
  }
}

$Audit | ConvertTo-Json -Depth 12 | Set-Content -Path $ResultPath -Encoding UTF8

$Report = @(
  "# TY142 Final Integration Readiness",
  "",
  "- Status: $Status",
  "- Backend root exists: $($Paths.backend_root.exists)",
  "- Frontend root exists: $($Paths.frontend_root.exists)",
  "- Backend config exists: $($Paths.backend_config.exists)",
  "- Backend tests folder exists: $($Paths.backend_tests.exists)",
  "- Frontend package.json exists: $($Paths.frontend_package.exists)",
  "- Any local endpoint reachable: $($Readiness.any_endpoint_reachable)",
  "- Secret values logged: false",
  "",
  "## Missing / Follow-up Items",
  ($Missing | ForEach-Object { "- $_" }),
  "",
  "## Output",
  "- Result JSON: $ResultPath"
)
$Report | Set-Content -Path $ReportPath -Encoding UTF8

Write-Host "TY142_FINAL_INTEGRATION_READINESS_COMPLETE"
exit 0
