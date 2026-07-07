$ErrorActionPreference = 'Stop'

# AAYS aays1 site-visible program sync task
# This script is intentionally limited to docs/chatgpt_status/aays1/* outputs.
# It does not write DB, run migrations, deploy production, or mark final_ready=true.

$TaskId = 'aays1-visible-program-sync-20260708'
$PageKey = 'aays1'
$UtcNow = (Get-Date).ToUniversalTime().ToString('o')

$PageRoot = Resolve-Path (Join-Path $PSScriptRoot '..')
$StatusDir = Join-Path $PageRoot 'status'
$ReportsDir = Join-Path $PageRoot 'reports'
$HeartbeatDir = Join-Path $PageRoot 'heartbeat'
$RunnerOutputsDir = Join-Path $PageRoot 'runner_outputs'

New-Item -ItemType Directory -Force -Path $StatusDir, $ReportsDir, $HeartbeatDir, $RunnerOutputsDir | Out-Null

$StatusPath = Join-Path $StatusDir 'aays1_site_visible_current_status_20260708.json'
$LatestStatusPath = Join-Path $StatusDir 'aays1_site_visible_current_status_latest.json'
$ReportPath = Join-Path $ReportsDir 'aays1_visible_program_sync_20260708.md'
$HeartbeatPath = Join-Path $HeartbeatDir 'aays1_visible_program_sync_heartbeat_latest.txt'
$RunnerOutputPath = Join-Path $RunnerOutputsDir 'aays1_visible_program_sync_20260708_runner_output.txt'

$status = [ordered]@{
  page_key = $PageKey
  task_id = $TaskId
  checked_at = $UtcNow
  status = 'runner_processed_site_visible_sync'
  user_visible_summary = 'aays1 page plan has been queued and synchronized into site-visible status/report outputs; product final remains false.'
  runner_expectation = 'single_shared_stable_runner_only'
  expected_repo_root = 'C:\AAYS_WT\AAYS_RUNNER_HEALTHY_20260707'
  expected_branch = 'codex/aays-single-runner-v5-20260706'
  site_visible_outputs = @(
    'docs/chatgpt_status/aays1/status/aays1_site_visible_current_status_latest.json',
    'docs/chatgpt_status/aays1/reports/aays1_visible_program_sync_20260708.md',
    'docs/chatgpt_status/aays1/heartbeat/aays1_visible_program_sync_heartbeat_latest.txt',
    'docs/chatgpt_status/aays1/runner_outputs/aays1_visible_program_sync_20260708_runner_output.txt'
  )
  completed = $false
  final_ready = $false
  product_final_ready = $false
  fake_data = $false
  db_write = $false
  migration = $false
  production_deploy = $false
  needs_runner_pickup_proof = $true
}

$json = $status | ConvertTo-Json -Depth 8
Set-Content -Path $StatusPath -Value $json -Encoding UTF8
Set-Content -Path $LatestStatusPath -Value $json -Encoding UTF8

$report = @"
# aays1 Site Visible Program Sync

- page_key: aays1
- task_id: $TaskId
- checked_at: $UtcNow
- status: runner_processed_site_visible_sync
- completed: false
- final_ready: false
- product_final_ready: false
- fake_data: false
- db_write: false
- migration: false
- production_deploy: false

## What this proves

This proves the aays1 page plan was converted into site-visible status/report outputs under the allowed aays1 path.

## What this does not prove

This does not mark the TerraYield/AAYS product final. It does not claim 100% completion. It still requires GitHub-visible shared runner pickup evidence from the stable runner.
"@
Set-Content -Path $ReportPath -Value $report -Encoding UTF8

Set-Content -Path $HeartbeatPath -Value "checked_at=$UtcNow; page_key=$PageKey; task_id=$TaskId; final_ready=false" -Encoding UTF8
Set-Content -Path $RunnerOutputPath -Value "AAYS aays1 visible program sync output written at $UtcNow. final_ready=false; fake_data=false; db_write=false; migration=false; production_deploy=false." -Encoding UTF8

Write-Output (@{
  page_key = $PageKey
  task_id = $TaskId
  status = 'runner_processed_site_visible_sync'
  final_ready = $false
  fake_data = $false
  db_write = $false
  migration = $false
  production_deploy = $false
} | ConvertTo-Json -Depth 5)
