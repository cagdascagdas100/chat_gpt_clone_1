$ErrorActionPreference = "Stop"

$BridgeRoot = "C:\AAYS_GITHUB_BRIDGE\chat_gpt_clone_1"
$Backend = "C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence"
$Frontend = "C:\Users\cagda\Documents\GitHub\AAYS\england_map_web"
$PlannedDataRoot = "E:\AAYS_DATA\planlanan yapılar"
$ResultsDir = Join-Path $BridgeRoot "ai-results"

New-Item -ItemType Directory -Force -Path $ResultsDir | Out-Null

$Audit = [ordered]@{
  task_id = "ty-pdi-020-oneshot-v2-selftest"
  status = "completed"
  generated_at = (Get-Date).ToString("s")
  bridge_root = $BridgeRoot
  backend_exists = Test-Path -Path $Backend
  frontend_exists = Test-Path -Path $Frontend
  planned_data_root_exists = Test-Path -Path $PlannedDataRoot
  policy = [ordered]@{
    no_repo_source_changes = $true
    fake_data_allowed = $false
    hardcoded_demo_data_allowed = $false
    official_structured_sources_priority = $true
    evidence_required_for_scores_and_timelines = $true
    estimated_language_required_when_exact_dates_missing = $true
  }
}

$Audit | ConvertTo-Json -Depth 8 | Set-Content -Path (Join-Path $ResultsDir "ty-pdi-020-oneshot-v2-selftest.audit.json") -Encoding UTF8

Write-Host "ONESHOT_V2_SELFTEST_COMPLETE"
exit 0
