$ErrorActionPreference = 'Stop'
$Page = 'AAYS_REAL_TOPOGRAPHY_PRODUCT'
$Branch = 'aays-runner-v17-icon-work-20260603-232706'
$Now = Get-Date -Format yyyyMMdd-HHmmss
$Root = Join-Path (Get-Location) "docs/chatgpt_status/$Page"
$Reports = Join-Path $Root 'reports'
$Status = Join-Path $Root 'status'
$Heartbeat = Join-Path $Root 'heartbeat'
New-Item -ItemType Directory -Force -Path $Reports,$Status,$Heartbeat | Out-Null
$Report = Join-Path $Reports "runner_target_branch_contract_probe_$Now.txt"
"PAGE_KEY=$Page`nMODE=TARGET_BRANCH_CONTRACT_PROBE`nBRANCH=$Branch`nPRODUCT_PROGRESS_ESTIMATE=99`nFINAL_READY=False`nEXPECTED_FINAL_REPORT=docs/chatgpt_status/$Page/reports/topography_real_lookup_endpoint_smoke_<timestamp>.txt`nNO_FAKE_DATA=True`nDB_WRITE=False`nMIGRATION=False`nDEPLOY=False`n" | Set-Content $Report -Encoding UTF8
"This probe confirms that the target branch runner contract file was consumed. It does not mark FINAL_READY by itself." | Add-Content $Report
"PAGE_KEY=$Page`nSTATUS=TARGET_BRANCH_CONTRACT_PROBE_WRITTEN`nPRODUCT_PROGRESS_ESTIMATE=99`nFINAL_READY=False`nLATEST_REPORT=docs/chatgpt_status/$Page/reports/runner_target_branch_contract_probe_$Now.txt`nEXPECTED_FINAL_REPORT=docs/chatgpt_status/$Page/reports/topography_real_lookup_endpoint_smoke_<timestamp>.txt`n" | Set-Content (Join-Path $Status "chatgpt_progress_99_target_branch_contract_probe_$Now.txt") -Encoding UTF8
"PAGE_KEY=$Page`nHEARTBEAT_AT=$Now`nSTATUS=TARGET_BRANCH_CONTRACT_PROBE_WRITTEN`n" | Set-Content (Join-Path $Heartbeat "heartbeat_target_branch_contract_probe_$Now.txt") -Encoding UTF8
