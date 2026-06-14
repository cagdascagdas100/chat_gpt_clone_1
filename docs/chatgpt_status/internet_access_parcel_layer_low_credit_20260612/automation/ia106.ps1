$r=Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..')
$reports=Join-Path $r 'docs\chatgpt_status\reports'
$status=Join-Path $r 'docs\chatgpt_status\internet_access_parcel_layer_low_credit_20260612\status'
New-Item -ItemType Directory -Force $reports,$status | Out-Null
$payload=[ordered]@{task_id='ia106';page_key='internet_access_parcel_layer_low_credit_20260612';status='RUNNER_DIAG_READY';completion_percent=80;final_ready=$false;check_105='docs/chatgpt_status/reports/internet-access-105-shared-runner-package-and-validate.json'}
($payload|ConvertTo-Json -Depth 4)|Set-Content (Join-Path $reports 'ia106.json') -Encoding UTF8
'ia106=RUNNER_DIAG_READY'|Set-Content (Join-Path $status 'ia106.txt') -Encoding UTF8