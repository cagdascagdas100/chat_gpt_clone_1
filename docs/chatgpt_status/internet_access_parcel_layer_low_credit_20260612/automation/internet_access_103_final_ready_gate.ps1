$ErrorActionPreference = 'Stop'

$Repo = 'C:\Users\cagda\Documents\GitHub\AAYS'
$Branch = 'feature/terrayield-aays-integration'
$PageKey = 'internet_access_parcel_layer_low_credit_20260612'
$TaskId = 'internet-access-103-final-ready-gate'
$WorkRoot = 'F:\chatgpt\AAYS_WORK\internet_access_score10_real_build_20260610'

$ReportDir = Join-Path $Repo 'docs\chatgpt_status\reports'
$StatusDir = Join-Path $Repo ("docs\chatgpt_status\$PageKey\status")
$HeartbeatDir = Join-Path $Repo ("docs\chatgpt_status\$PageKey\heartbeat")
New-Item -ItemType Directory -Force -Path $ReportDir,$StatusDir,$HeartbeatDir | Out-Null

$Stamp = Get-Date -Format 'yyyyMMddTHHmmss'
$ReportJson = Join-Path $ReportDir 'internet-access-103-final-ready-gate.json'
$ReportTxt = Join-Path $ReportDir 'internet-access-103-final-ready-gate.txt'
$StatusJson = Join-Path $StatusDir "internet-access-103-final-ready-gate-$Stamp.json"
$HeartbeatTxt = Join-Path $HeartbeatDir "internet-access-103-final-ready-gate-$Stamp.txt"

$Expected101Json = Join-Path $ReportDir 'internet-access-101-safe-nested-zip-transform.json'
$Expected101Txt = Join-Path $ReportDir 'internet-access-101-safe-nested-zip-transform.txt'
$Expected102Json = Join-Path $ReportDir 'internet-access-102-safe-final-validation.json'
$Expected102Txt = Join-Path $ReportDir 'internet-access-102-safe-final-validation.txt'

$paths = [ordered]@{
  expected_101_json = $Expected101Json
  expected_101_txt = $Expected101Txt
  expected_102_json = $Expected102Json
  expected_102_txt = $Expected102Txt
  work_root = $WorkRoot
}

$exists = [ordered]@{}
foreach ($k in $paths.Keys) { $exists[$k] = Test-Path $paths[$k] }

$missing = @()
foreach ($k in @('expected_101_json','expected_101_txt','expected_102_json','expected_102_txt')) {
  if (-not $exists[$k]) { $missing += $k }
}

$status = 'FINAL_READY'
$completion = 100
$nextAction = 'none'
if ($missing.Count -gt 0) {
  $status = 'BLOCKED_WAITING_FOR_101_102_REPORTS'
  $completion = 60
  $nextAction = 'single shared runner must run queued Internet Access 101/102 automation first'
}

$result = [ordered]@{
  generated_at = (Get-Date).ToString('o')
  page_key = $PageKey
  task_id = $TaskId
  branch = $Branch
  status = $status
  completion_percent = $completion
  missing = $missing
  exists = $exists
  expected_reports = @(
    'docs/chatgpt_status/reports/internet-access-101-safe-nested-zip-transform.json',
    'docs/chatgpt_status/reports/internet-access-101-safe-nested-zip-transform.txt',
    'docs/chatgpt_status/reports/internet-access-102-safe-final-validation.json',
    'docs/chatgpt_status/reports/internet-access-102-safe-final-validation.txt',
    'docs/chatgpt_status/reports/internet-access-103-final-ready-gate.json',
    'docs/chatgpt_status/reports/internet-access-103-final-ready-gate.txt'
  )
  data_policy = 'official_or_verified_only_no_fake_data'
  parallel_safety = 'read_only_gate_after_101_102_reports_no_db_write_no_runner_spawn'
  next_action = $nextAction
  manual_stdout_required = $false
  powershell_required = $false
}

$result | ConvertTo-Json -Depth 8 | Set-Content -Path $ReportJson -Encoding UTF8
$result | ConvertTo-Json -Depth 8 | Set-Content -Path $StatusJson -Encoding UTF8
@"
Internet Access 103 final ready gate
Generated: $($result.generated_at)
Page key: $PageKey
Status: $status
Completion percent: $completion
Missing: $($missing -join ', ')
Next action: $nextAction
Manual stdout required: false
"@ | Set-Content -Path $ReportTxt -Encoding UTF8
"$TaskId $status $completion" | Set-Content -Path $HeartbeatTxt -Encoding UTF8

Set-Location $Repo
git add docs/chatgpt_status/reports/internet-access-103-final-ready-gate.json docs/chatgpt_status/reports/internet-access-103-final-ready-gate.txt "docs/chatgpt_status/$PageKey/status" "docs/chatgpt_status/$PageKey/heartbeat"
git commit -m "Internet Access 103 final ready gate report" | Out-Null
git push origin $Branch | Out-Null
