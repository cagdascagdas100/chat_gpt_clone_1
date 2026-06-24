$ErrorActionPreference = "Stop"
$Repo = "C:\Users\cagda\Documents\GitHub\AAYS"
$PageKey = "gas_emissions"
$Ts = "20260625_002326"
Set-Location $Repo

$now = Get-Date -Format o
"runner_pickup=proven
started_at=$now
page_key=$PageKey" | Set-Content -Encoding UTF8 "C:\Users\cagda\Documents\GitHub\AAYS\docs\chatgpt_status\gas_emissions\runner_outputs\gas_emissions_runner_probe_output_20260625_002326.txt"

@{
  status="RUNNER_PICKUP_PROVEN"
  page_key=$PageKey
  final_ready=$false
  percent=89
  reason="runner picked the task; final acceptance evidence still required"
  timestamp=$now
} | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 "C:\Users\cagda\Documents\GitHub\AAYS\docs\chatgpt_status\gas_emissions\status\gas_emissions_runner_probe_status_20260625_002326.json"

@{
  heartbeat="RUNNER_PICKUP_PROVEN"
  page_key=$PageKey
  timestamp=$now
  final_ready=$false
} | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 "C:\Users\cagda\Documents\GitHub\AAYS\docs\chatgpt_status\gas_emissions\heartbeat\gas_emissions_runner_probe_heartbeat_20260625_002326.json"

@"
# gas_emissions runner probe result

status=RUNNER_PICKUP_PROVEN
page_key=gas_emissions
final_ready=false
percent=89
reason=runner picked task; finalizer runtime evidence still required
timestamp=$now

Expected final report:
docs/chatgpt_status/gas_emissions/reports/gas_emissions_finalizer_result_20260622_2300.md
