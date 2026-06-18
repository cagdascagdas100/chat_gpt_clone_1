$ErrorActionPreference='Continue'
$Root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$ReportDir = Join-Path $Root 'reports'
$StatusDir = Join-Path $Root 'status'
New-Item -ItemType Directory -Force -Path $ReportDir,$StatusDir | Out-Null
$Report = Join-Path $ReportDir 'runner_poll_selfcheck_20260618_010.txt'
$Status = Join-Path $StatusDir 'runner_poll_selfcheck_status_20260618_010.txt'
$lines = @()
$lines += 'page_key=aays1'
$lines += 'diagnostic=runner_poll_selfcheck'
$lines += 'product_final_proof=false'
$lines += 'runner_executed_selfcheck=true'
$lines += ('utc=' + (Get-Date).ToUniversalTime().ToString('s') + 'Z')
$lines += ('pwd=' + (Get-Location).Path)
$lines += ('script_path=' + $PSCommandPath)
$lines += ('expected_product_task=docs/chatgpt_status/aays1/automation/future_growth_100_db_layer_ui_smoke_20260616_001.ps1')
$lines += 'next_action=shared_runner_should_execute_product_task_and_write_future_growth_100_status_latest'
$lines | Set-Content -Encoding UTF8 $Report
$lines | Set-Content -Encoding UTF8 $Status
exit 0
