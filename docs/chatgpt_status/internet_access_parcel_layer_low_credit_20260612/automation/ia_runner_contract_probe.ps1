$root=Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..')
$page='internet_access_parcel_layer_low_credit_20260612'
$status=Join-Path $root "docs\chatgpt_status\$page\status"
$reports=Join-Path $root 'docs\chatgpt_status\reports'
New-Item -ItemType Directory -Force $status,$reports | Out-Null
$paths=@(
  'docs/chatgpt_status/current-task.txt',
  "docs/chatgpt_status/$page/current-task.txt",
  "docs/chatgpt_status/$page/queue/ia106.txt",
  "docs/chatgpt_status/$page/runner_tasks/ia106.txt",
  "docs/chatgpt_status/$page/queue/internet-access-105-shared-runner-package-and-validate.txt",
  "docs/chatgpt_status/$page/runner_tasks/ia105.txt",
  "docs/chatgpt_status/$page/queue/internet-access-107-final-ready-gate.txt",
  "docs/chatgpt_status/$page/runner_tasks/ia107.txt"
)
$obj=[ordered]@{
  task_id='ia-contract-probe'
  page_key=$page
  status='PROBE_READY'
  checked_paths=$paths
  expected_first_report='docs/chatgpt_status/reports/ia106.json'
  completion_percent=99
  final_ready=$false
}
$obj | ConvertTo-Json -Depth 5 | Out-File (Join-Path $status 'ia-runner-contract-probe.json') -Encoding utf8
$obj | ConvertTo-Json -Depth 5 | Out-File (Join-Path $reports 'ia-runner-contract-probe.json') -Encoding utf8
