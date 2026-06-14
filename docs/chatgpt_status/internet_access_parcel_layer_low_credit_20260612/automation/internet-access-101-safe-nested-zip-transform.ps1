$PageKey='internet_access_parcel_layer_low_credit_20260612'
$TaskId='internet-access-101-safe-nested-zip-transform'
$RepoRoot=Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..')
$ReportsDir=Join-Path $RepoRoot 'docs\chatgpt_status\reports'
$StatusDir=Join-Path $RepoRoot "docs\chatgpt_status\$PageKey\status"
New-Item -ItemType Directory -Force $ReportsDir,$StatusDir | Out-Null
$Report=Join-Path $ReportsDir "$TaskId.json"
$StatusFile=Join-Path $StatusDir "$TaskId.txt"
$Payload=[ordered]@{
  task_id=$TaskId
  page_key=$PageKey
  status='WAITING_SOURCE_ARTIFACT_OR_PRIOR_PACKAGE'
  completion_percent=50
  manual_stdout_required=$false
  expected_next_report='docs/chatgpt_status/reports/internet-access-102-safe-final-validation.json'
  power_shell_required=$false
}
($Payload | ConvertTo-Json -Depth 4) | Set-Content $Report -Encoding UTF8
"task_id=$TaskId`npage_key=$PageKey`nstatus=WAITING_SOURCE_ARTIFACT_OR_PRIOR_PACKAGE`ncompletion_percent=50`nmanual_stdout_required=false`npower_shell_required=false" | Set-Content $StatusFile -Encoding UTF8
