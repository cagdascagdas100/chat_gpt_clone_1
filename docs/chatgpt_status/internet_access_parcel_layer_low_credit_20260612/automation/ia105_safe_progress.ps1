$root=Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..')
$reports=Join-Path $root 'docs\chatgpt_status\reports'
$statusDir=Join-Path $root 'docs\chatgpt_status\internet_access_parcel_layer_low_credit_20260612\status'
New-Item -ItemType Directory -Force $reports,$statusDir | Out-Null
$dep=Join-Path $reports 'ia106.json'
$ready=Test-Path $dep
$obj=[ordered]@{
 task_id='internet-access-105-shared-runner-package-and-validate'
 page_key='internet_access_parcel_layer_low_credit_20260612'
 status=if($ready){'READY_FOR_107'}else{'WAITING_FOR_IA106'}
 completion_percent=if($ready){98}else{97}
 final_ready=$false
 manual_stdout_required=$false
 dependency_ia106_exists=$ready
 expected_next_report='docs/chatgpt_status/reports/internet-access-107-final-ready-gate.json'
}
$obj | ConvertTo-Json -Depth 4 | Out-File (Join-Path $reports 'internet-access-105-shared-runner-package-and-validate.json') -Encoding utf8
'ia105=safe_progress' | Out-File (Join-Path $statusDir 'ia105_safe_progress.txt') -Encoding utf8
