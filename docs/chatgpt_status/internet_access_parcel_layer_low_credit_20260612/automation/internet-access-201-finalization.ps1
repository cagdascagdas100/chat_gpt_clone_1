$ErrorActionPreference='Stop'
$PageKey='internet_access_parcel_layer_low_credit_20260612'
$TaskId='internet-access-201-finalization'
Set-Location (git rev-parse --show-toplevel)
$ReportDir="docs/chatgpt_status/$PageKey/reports"
$StatusDir="docs/chatgpt_status/$PageKey/status"
New-Item -ItemType Directory -Force $ReportDir,$StatusDir | Out-Null
$Stamp=Get-Date -Format yyyyMMddTHHmmss
$Result=[ordered]@{
  task_id=$TaskId
  page_key=$PageKey
  generated_at=(Get-Date).ToString('o')
  status='RUNNER_ACCEPTED_PAGE_KEY_AUTOMATION'
  completion_percent=35
  powershell_required=$false
  separate_runner_required=$false
  next_actions=@('run existing internet-access-101-safe-nested-zip-transform through shared runner','run final validation after report appears')
  expected_report='docs/chatgpt_status/reports/internet-access-101-safe-nested-zip-transform.json'
}
$Result | ConvertTo-Json -Depth 8 | Set-Content "$ReportDir/$TaskId.json" -Encoding UTF8
$Result | ConvertTo-Json -Depth 8 | Set-Content "$StatusDir/$TaskId-$Stamp.json" -Encoding UTF8
