$PageKey='gas_emissions'
$TaskId='terrayield-098-gas-emissions-slot-drift-probe'
$Root='docs/chatgpt_status/current-task.txt'
$Page='docs/chatgpt_status/gas_emissions/current-task.txt'
$Report='docs/chatgpt_status/gas_emissions/reports/terrayield-098-gas-emissions-slot-drift-probe.txt'
$Status='docs/chatgpt_status/gas_emissions/status/terrayield-098-gas-emissions-slot-drift-probe.txt'
New-Item -ItemType Directory -Force -Path (Split-Path $Report) | Out-Null
New-Item -ItemType Directory -Force -Path (Split-Path $Status) | Out-Null
$rootText = if (Test-Path $Root) { Get-Content $Root -Raw } else { 'MISSING_ROOT_CURRENT_TASK' }
$pageText = if (Test-Path $Page) { Get-Content $Page -Raw } else { 'MISSING_PAGE_CURRENT_TASK' }
$rootHasGas = $rootText -match 'gas_emissions'
$pageHasGas = $pageText -match 'gas_emissions'
$drift = -not $rootHasGas -and $pageHasGas
$lines = @()
$lines += 'page_key=gas_emissions'
$lines += 'task_id=terrayield-098-gas-emissions-slot-drift-probe'
$lines += 'status=PROBED'
$lines += "root_has_gas_emissions=$rootHasGas"
$lines += "page_has_gas_emissions=$pageHasGas"
$lines += "slot_drift_detected=$drift"
$lines += 'writes_product_output=false'
$lines += 'final_ready=false'
$lines | Set-Content -Path $Report -Encoding UTF8
$lines | Set-Content -Path $Status -Encoding UTF8
