$PageKey='internet_access_parcel_layer_low_credit_20260612'
$TaskId='internet-access-107-final-ready-gate'
$RepoRoot=Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..')
$ReportsDir=Join-Path $RepoRoot 'docs\chatgpt_status\reports'
$StatusDir=Join-Path $RepoRoot "docs\chatgpt_status\$PageKey\status"
New-Item -ItemType Directory -Force $ReportsDir,$StatusDir | Out-Null
$Report=Join-Path $ReportsDir "$TaskId.json"
$StatusFile=Join-Path $StatusDir "$TaskId.txt"
$Dep106=Join-Path $ReportsDir 'ia106.json'
$Dep105=Join-Path $ReportsDir 'internet-access-105-shared-runner-package-and-validate.json'
$Dep106Ready=Test-Path $Dep106
$Dep105Ready=Test-Path $Dep105
$status=if($Dep106Ready -and $Dep105Ready){'FINAL_READY'}else{'BLOCKED_WAITING_FINAL_REPORTS'}
$percent=if($status -eq 'FINAL_READY'){100}else{94}
$payload=[ordered]@{
  task_id=$TaskId
  page_key=$PageKey
  status=$status
  completion_percent=$percent
  manual_stdout_required=$false
  dependency_ia106_exists=$Dep106Ready
  dependency_105_exists=$Dep105Ready
  expected_ready_report='docs/chatgpt_status/reports/internet-access-107-final-ready-gate.json'
  power_shell_required=$false
}
($payload | ConvertTo-Json -Depth 4) | Set-Content $Report -Encoding UTF8
"task_id=$TaskId`npage_key=$PageKey`nstatus=$status`ncompletion_percent=$percent`nmanual_stdout_required=false`npower_shell_required=false" | Set-Content $StatusFile -Encoding UTF8
