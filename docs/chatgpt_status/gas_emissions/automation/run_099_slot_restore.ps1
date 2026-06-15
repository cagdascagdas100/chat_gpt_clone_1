$root = 'docs/chatgpt_status/current-task.txt'
$report = 'docs/chatgpt_status/gas_emissions/reports/terrayield-099-gas-emissions-slot-restore.txt'
$status = 'docs/chatgpt_status/gas_emissions/status/terrayield-099-gas-emissions-slot-restore.txt'
New-Item -ItemType Directory -Force -Path (Split-Path $report) | Out-Null
New-Item -ItemType Directory -Force -Path (Split-Path $status) | Out-Null
$body = @'
task_id=terrayield-088-gas-emissions-proxy-finalize
status=QUEUED
branch=feature/terrayield-aays-integration
runner_task=docs/chatgpt_status/gas_emissions/automation/run_088_proxy_finalize.ps1
expected_report=docs/chatgpt_status/gas_emissions/reports/terrayield-088-gas-emissions-proxy-finalize.txt
manual_stdout_required=false
page_key=gas_emissions
completion_percent=99
final_ready=false
'@
Set-Content -Path $root -Value $body -Encoding UTF8
$line = "slot_restore_written=true`nroot_file=$root`npage_key=gas_emissions`ntarget_task=terrayield-088-gas-emissions-proxy-finalize`nfinal_ready=false"
Set-Content -Path $report -Value $line -Encoding UTF8
Set-Content -Path $status -Value $line -Encoding UTF8
