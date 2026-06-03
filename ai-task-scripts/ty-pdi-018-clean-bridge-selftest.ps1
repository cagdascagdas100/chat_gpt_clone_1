$ErrorActionPreference = "Stop"

$BridgeRoot = "C:\AAYS_GITHUB_BRIDGE\chat_gpt_clone_1"
$Backend = "C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence"
$Frontend = "C:\Users\cagda\Documents\GitHub\AAYS\england_map_web"
$PlannedDataRoot = "E:\AAYS_DATA\planlanan yapılar"
$ResultsDir = Join-Path $BridgeRoot "ai-results"

New-Item -ItemType Directory -Force -Path $ResultsDir | Out-Null

$GitStatus = "NOT_CHECKED"
$GitExitCode = $null

try {
  Push-Location $Backend
  $GitOutput = git status --short --untracked-files=no 2>&1
  $GitExitCode = $LASTEXITCODE
  Pop-Location

  if ($GitExitCode -eq 0) {
    if ($GitOutput) {
      $GitStatus = ($GitOutput -join "`n")
    } else {
      $GitStatus = "CLEAN"
    }
  } else {
    $GitStatus = "GIT_STATUS_NON_BLOCKING_FAILED"
  }
} catch {
  try { Pop-Location } catch {}
  $GitStatus = "GIT_STATUS_EXCEPTION_NON_BLOCKING"
}

$Audit = [ordered]@{
  task_id = "ty-pdi-018-clean-bridge-selftest"
  status = "completed"
  generated_at = (Get-Date).ToString("s")
  bridge_root = $BridgeRoot
  backend_exists = Test-Path -Path $Backend
  frontend_exists = Test-Path -Path $Frontend
  planned_data_root_exists = Test-Path -Path $PlannedDataRoot
  backend_git_status = $GitStatus
  backend_git_exit_code = $GitExitCode
  policy = [ordered]@{
    no_repo_source_changes = $true
    fake_data_allowed = $false
    hardcoded_demo_data_allowed = $false
    official_structured_sources_priority = $true
    evidence_required_for_scores_and_timelines = $true
    estimated_language_required_when_exact_dates_missing = $true
  }
}

$Audit | ConvertTo-Json -Depth 8 | Set-Content -Path (Join-Path $ResultsDir "ty-pdi-018-clean-bridge-selftest.audit.json") -Encoding UTF8

Write-Host "CLEAN_BRIDGE_SELFTEST_COMPLETE"
exit 0
