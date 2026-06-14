$ErrorActionPreference = "Stop"
$PageKey = "internet_access_parcel_layer_low_credit_20260612"
$TaskId = "internet-access-104-shared-runner-finalize"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..\..\..\..")
$ReportDir = Join-Path $Root "docs\chatgpt_status\reports"
$StatusDir = Join-Path $Root "docs\chatgpt_status\$PageKey\status"
New-Item -ItemType Directory -Force $ReportDir, $StatusDir | Out-Null
$r101 = Join-Path $ReportDir "internet-access-101-safe-nested-zip-transform.json"
$r102 = Join-Path $ReportDir "internet-access-102-safe-final-validation.json"
$pct = 30
$status = "WAITING_FOR_REPORTS"
if (Test-Path $r101) { $pct = 60; $status = "REPORT_101_PRESENT" }
if ((Test-Path $r101) -and (Test-Path $r102)) { $pct = 80; $status = "REPORT_102_PRESENT" }
$report = "task_id=$TaskId`npage_key=$PageKey`nstatus=$status`ncompletion_percent=$pct`nmanual_stdout_required=false`n"
$report | Set-Content (Join-Path $ReportDir "$TaskId.txt") -Encoding UTF8
$report | Set-Content (Join-Path $StatusDir "$TaskId.txt") -Encoding UTF8
