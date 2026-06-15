$root=Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..')
$reports=Join-Path $root 'docs\chatgpt_status\reports'
$statusDir=Join-Path $root 'docs\chatgpt_status\internet_access_parcel_layer_low_credit_20260612\status'
New-Item -ItemType Directory -Force $reports,$statusDir | Out-Null
$dep106=Test-Path (Join-Path $reports 'ia106.json')
$dep105=Test-Path (Join-Path $reports 'internet-access-105-shared-runner-package-and-validate.json')
$ready=($dep106 -and $dep105)
$obj=[ordered]@{
 task_id='internet-access-107-final-ready-gate'
 page_key='internet_access_parcel_layer_low_credit_20260612'
 status=if($ready){'FINAL_READY'}else{'WAITING_FOR_DEPENDENCIES'}
 completion_percent=if($ready){100}else{98}
 final_ready=$ready
 manual_stdout_required=$false
 dependency_ia106_exists=$dep106
 dependency_105_exists=$dep105
}
$obj | ConvertTo-Json -Depth 4 | Out-File (Join-Path $reports 'internet-access-107-final-ready-gate.json') -Encoding utf8
'ia107=safe_final_gate' | Out-File (Join-Path $statusDir 'ia107_safe_final_gate.txt') -Encoding utf8
