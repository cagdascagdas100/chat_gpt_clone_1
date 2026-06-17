$ErrorActionPreference='Stop'
$root=(Get-Location).Path
$dir=Join-Path $root 'docs/chatgpt_status/gas_emissions/reports'
$out=Join-Path $root 'docs/chatgpt_status/gas_emissions/runner_outputs'
New-Item -ItemType Directory -Force -Path $dir,$out | Out-Null
$report=Join-Path $dir 'terrayield-094-pickup-probe.txt'
$json=Join-Path $out 'gas_emissions_094_pickup_probe_latest.json'
$final=Join-Path $dir 'terrayield-093-gas-emissions-contract-runtime-finalize.txt'
$rootTask=Join-Path $root 'docs/chatgpt_status/current-task.txt'
$now=(Get-Date).ToString('s')
$rootHead='missing'
if(Test-Path $rootTask){$rootHead=(Get-Content $rootTask -TotalCount 8) -join ' | '}
$finalExists=Test-Path $final
@("status=PICKED_UP","page_key=gas_emissions","task_id=terrayield-094-pickup-probe","timestamp=$now","final_093_exists=$finalExists","root_current_task=$rootHead","power_shell_required=false") | Set-Content -Encoding UTF8 $report
('{"status":"PICKED_UP","page_key":"gas_emissions","task_id":"terrayield-094-pickup-probe","final_093_exists":'+($finalExists.ToString().ToLower())+',"power_shell_required":false}') | Set-Content -Encoding UTF8 $json
