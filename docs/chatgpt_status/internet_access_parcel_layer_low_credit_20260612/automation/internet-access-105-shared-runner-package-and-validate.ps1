$PageKey='internet_access_parcel_layer_low_credit_20260612'
$TaskId='internet-access-105-shared-runner-package-and-validate'
$RepoRoot=Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..')
$ReportsDir=Join-Path $RepoRoot 'docs\chatgpt_status\reports'
$StatusDir=Join-Path $RepoRoot "docs\chatgpt_status\$PageKey\status"
New-Item -ItemType Directory -Force $ReportsDir,$StatusDir | Out-Null
$Report=Join-Path $ReportsDir "$TaskId.json"
$StatusFile=Join-Path $StatusDir "$TaskId.txt"
'{"task_id":"internet-access-105-shared-runner-package-and-validate","page_key":"internet_access_parcel_layer_low_credit_20260612","status":"QUEUED_FOR_SHARED_RUNNER","completion_percent":35,"manual_stdout_required":false}' | Set-Content $Report -Encoding UTF8
"task_id=$TaskId`npage_key=$PageKey`nstatus=QUEUED_FOR_SHARED_RUNNER`ncompletion_percent=35`nmanual_stdout_required=false" | Set-Content $StatusFile -Encoding UTF8
