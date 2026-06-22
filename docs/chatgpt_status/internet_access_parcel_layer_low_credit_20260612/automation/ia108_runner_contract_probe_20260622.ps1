$ErrorActionPreference = 'Stop'
$pageKey = 'internet_access_parcel_layer_low_credit_20260612'
$repoRoot = (Get-Location).Path
$pageRoot = Join-Path $repoRoot "docs/chatgpt_status/$pageKey"
$reportDir = Join-Path $pageRoot 'reports'
$statusDir = Join-Path $pageRoot 'status'
$heartbeatDir = Join-Path $pageRoot 'heartbeat'
$runnerOutDir = Join-Path $pageRoot 'runner_outputs'
foreach ($dir in @($reportDir, $statusDir, $heartbeatDir, $runnerOutDir)) {
  if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
}
$now = (Get-Date).ToUniversalTime().ToString('o')
$payload = [ordered]@{
  task_id = 'ia108-runner-contract-probe-20260622'
  page_key = $pageKey
  status = 'RUNNER_CONTRACT_PROBE_OK'
  generated_at_utc = $now
  runner_workdir = $repoRoot
  expected_next_product_task = 'docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/automation/ia108_real_geometry_join_v2_schema_probe.ps1'
  writes_reports = $true
  requires_manual_stdout = $false
  db_write = $false
  migration = $false
  production_deploy = $false
  fake_data = $false
}
$json = ($payload | ConvertTo-Json -Depth 8)
$reportPath = Join-Path $reportDir 'ia108_runner_contract_probe_20260622.json'
$statusPath = Join-Path $statusDir 'ia108_runner_contract_probe_20260622.status.txt'
$heartbeatPath = Join-Path $heartbeatDir 'ia108_runner_contract_probe_20260622.heartbeat.txt'
$outputPath = Join-Path $runnerOutDir 'ia108_runner_contract_probe_20260622.out.txt'
Set-Content -Path $reportPath -Encoding UTF8 -Value $json
Set-Content -Path $statusPath -Encoding UTF8 -Value 'RUNNER_CONTRACT_PROBE_OK'
Set-Content -Path $heartbeatPath -Encoding UTF8 -Value $now
Set-Content -Path $outputPath -Encoding UTF8 -Value "runner contract probe completed at $now"
Write-Host "RUNNER_CONTRACT_PROBE_OK $reportPath"