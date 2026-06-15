$root=Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..')
$reports=Join-Path $root 'docs\chatgpt_status\reports'
$statusDir=Join-Path $root 'docs\chatgpt_status\internet_access_parcel_layer_low_credit_20260612\status'
New-Item -ItemType Directory -Force $reports,$statusDir | Out-Null
$obj=[ordered]@{
  task_id='ia106'
  page_key='internet_access_parcel_layer_low_credit_20260612'
  status='READY_FOR_105'
  completion_percent=97
  final_ready=$false
  manual_stdout_required=$false
  expected_next_report='docs/chatgpt_status/reports/internet-access-105-shared-runner-package-and-validate.json'
}
$obj | ConvertTo-Json -Depth 4 | Out-File (Join-Path $reports 'ia106.json') -Encoding utf8
'ia106=READY_FOR_105' | Out-File (Join-Path $statusDir 'ia106.txt') -Encoding utf8
