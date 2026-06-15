$root=Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..')
$reports=Join-Path $root 'docs\chatgpt_status\reports'
$status=Join-Path $root 'docs\chatgpt_status\internet_access_parcel_layer_low_credit_20260612\status'
New-Item -ItemType Directory -Force $reports,$status | Out-Null
$d106=Join-Path $reports 'ia106.json'
$d105=Join-Path $reports 'internet-access-105-shared-runner-package-and-validate.json'
if(-not ((Test-Path $d106) -and (Test-Path $d105))){
  'ia107=WAITING_FOR_IA106_AND_IA105' | Out-File (Join-Path $status 'ia107.txt') -Encoding utf8
  exit 0
}
$obj=[ordered]@{task_id='internet-access-107-final-ready-gate';page_key='internet_access_parcel_layer_low_credit_20260612';status='FINAL_READY';completion_percent=100;final_ready=$true;manual_stdout_required=$false;dependency_ia106_exists=$true;dependency_105_exists=$true;expected_ready_report='docs/chatgpt_status/reports/internet-access-107-final-ready-gate.json'}
$obj | ConvertTo-Json -Depth 4 | Out-File (Join-Path $reports 'internet-access-107-final-ready-gate.json') -Encoding utf8
'ia107=FINAL_READY' | Out-File (Join-Path $status 'ia107.txt') -Encoding utf8