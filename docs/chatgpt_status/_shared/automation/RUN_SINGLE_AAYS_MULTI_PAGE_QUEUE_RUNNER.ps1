$PageKey='planned-buildings-codex-20260622'
$Script="docs/chatgpt_status/$PageKey/automation/planned_buildings_contract_detector_latest.ps1"
if(!(Test-Path $Script)){throw "missing $Script"}
powershell -NoProfile -ExecutionPolicy Bypass -File $Script
