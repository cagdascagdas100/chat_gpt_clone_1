$ErrorActionPreference = 'Stop'
$PageKey = 'gas_emissions'
$TaskId = 'terrayield-088-gas-emissions-proxy-finalize'
$ReportDir = "docs/chatgpt_status/$PageKey/reports"
$StatusDir = "docs/chatgpt_status/$PageKey/status"
$RunnerInput = 'docs/chatgpt_status/runner_inputs/terrayield-088-gas-emissions-proxy-finalize.ps1'
New-Item -ItemType Directory -Force $ReportDir,$StatusDir | Out-Null
$Report = Join-Path $ReportDir "$TaskId.txt"
"page_key=$PageKey`ntask_id=$TaskId`nautomation_path=docs/chatgpt_status/$PageKey/automation/run_088_proxy_finalize.ps1`nrunner_input=$RunnerInput" | Set-Content -Encoding UTF8 $Report
& $RunnerInput *>> $Report
"runner_exit_code=$LASTEXITCODE" | Add-Content -Encoding UTF8 $Report
"status=EXECUTED`nreport=$Report" | Set-Content -Encoding UTF8 (Join-Path $StatusDir "$TaskId.txt")
