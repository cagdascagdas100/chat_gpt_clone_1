$PageKey='internet_access_parcel_layer_low_credit_20260612'
$TaskId='internet-access-105-shared-runner-package-and-validate'
$RepoRoot=Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..')
$ReportsDir=Join-Path $RepoRoot 'docs\chatgpt_status\reports'
$StatusDir=Join-Path $RepoRoot "docs\chatgpt_status\$PageKey\status"
New-Item -ItemType Directory -Force $ReportsDir,$StatusDir | Out-Null
$Report=Join-Path $ReportsDir "$TaskId.json"
$StatusFile=Join-Path $StatusDir "$TaskId.txt"
$Dep101=Join-Path $ReportsDir 'internet-access-101-safe-nested-zip-transform.json'
$Dep102=Join-Path $ReportsDir 'internet-access-102-safe-final-validation.json'
$DepsReady=((Test-Path $Dep101) -and (Test-Path $Dep102))
$status=if($DepsReady){'READY_FOR_FINAL_VALIDATION'}else{'BLOCKED_WAITING_DEPENDENCY_REPORTS'}
$percent=if($DepsReady){70}else{40}
$payload=[ordered]@{
  task_id=$TaskId
  page_key=$PageKey
  status=$status
  completion_percent=$percent
  manual_stdout_required=$false
  expected_next_report='docs/chatgpt_status/reports/internet-access-105-shared-runner-package-and-validate.json'
  dependency_101_exists=(Test-Path $Dep101)
  dependency_102_exists=(Test-Path $Dep102)
  power_shell_required=$false
}
($payload | ConvertTo-Json -Depth 4) | Set-Content $Report -Encoding UTF8
"task_id=$TaskId`npage_key=$PageKey`nstatus=$status`ncompletion_percent=$percent`nmanual_stdout_required=false`npower_shell_required=false" | Set-Content $StatusFile -Encoding UTF8
