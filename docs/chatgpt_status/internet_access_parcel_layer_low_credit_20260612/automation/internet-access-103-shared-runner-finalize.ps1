$ErrorActionPreference = "Stop"

$PageKey = "internet_access_parcel_layer_low_credit_20260612"
$TaskId = "internet-access-103-shared-runner-finalize"
$Branch = "feature/terrayield-aays-integration"
$RepoRoot = (Resolve-Path ".").Path
$ReportsDir = Join-Path $RepoRoot "docs/chatgpt_status/reports"
$StatusDir = Join-Path $RepoRoot "docs/chatgpt_status/$PageKey/status"
$HeartbeatDir = Join-Path $RepoRoot "docs/chatgpt_status/$PageKey/heartbeat"
$WorkRoot = "F:\chatgpt\AAYS_WORK\internet_access_score10_real_build_20260610"

New-Item -ItemType Directory -Force $ReportsDir, $StatusDir, $HeartbeatDir | Out-Null

$runner101 = Join-Path $RepoRoot "docs/chatgpt_status/runner_inputs/internet-access-101-safe-nested-zip-transform.ps1"
$report101Json = Join-Path $ReportsDir "internet-access-101-safe-nested-zip-transform.json"
$report101Txt = Join-Path $ReportsDir "internet-access-101-safe-nested-zip-transform.txt"
$report102Json = Join-Path $ReportsDir "internet-access-102-safe-final-validation.json"
$report102Txt = Join-Path $ReportsDir "internet-access-102-safe-final-validation.txt"

$ran101 = $false
$errors = @()

try {
    if ((-not (Test-Path $report101Json)) -and (Test-Path $runner101)) {
        $ran101 = $true
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $runner101
    }
} catch {
    $errors += $_.Exception.Message
}

$report101Ready = (Test-Path $report101Json) -and (Test-Path $report101Txt)
$report102Ready = (Test-Path $report102Json) -and (Test-Path $report102Txt)
$finalReady = $report101Ready -and $report102Ready

if ($finalReady) {
    $status = "FINAL_READY"
    $completion = 100
} elseif ($report101Ready) {
    $status = "PROCESSED_PACKAGE_READY_SAFE_ARTIFACTS"
    $completion = 60
} else {
    $status = "BLOCKED_REPORTS_MISSING"
    $completion = 25
}

$result = [ordered]@{
    task_id = $TaskId
    page_key = $PageKey
    branch = $Branch
    generated_at = (Get-Date).ToString("o")
    status = $status
    completion_percent = $completion
    work_root = $WorkRoot
    ran_101_runner_input = $ran101
    report_101_json_exists = Test-Path $report101Json
    report_101_txt_exists = Test-Path $report101Txt
    report_102_json_exists = Test-Path $report102Json
    report_102_txt_exists = Test-Path $report102Txt
    expected_next_report_json = "docs/chatgpt_status/reports/internet-access-103-shared-runner-finalize.json"
    manual_stdout_required = $false
    errors = $errors
}

$outJson = Join-Path $ReportsDir "internet-access-103-shared-runner-finalize.json"
$outTxt = Join-Path $ReportsDir "internet-access-103-shared-runner-finalize.txt"
$statusJson = Join-Path $StatusDir "internet-access-103-shared-runner-finalize.json"
$heartbeatTxt = Join-Path $HeartbeatDir "internet-access-103-shared-runner-finalize.txt"

$result | ConvertTo-Json -Depth 8 | Set-Content -Path $outJson -Encoding UTF8
$result | ConvertTo-Json -Depth 8 | Set-Content -Path $statusJson -Encoding UTF8
@"
task_id=$TaskId
page_key=$PageKey
status=$status
completion_percent=$completion
report_101_json_exists=$($result.report_101_json_exists)
report_102_json_exists=$($result.report_102_json_exists)
manual_stdout_required=false
expected_next_report_json=docs/chatgpt_status/reports/internet-access-103-shared-runner-finalize.json
"@ | Set-Content -Path $outTxt -Encoding UTF8
@"
task_id=$TaskId
status=$status
completion_percent=$completion
generated_at=$($result.generated_at)
"@ | Set-Content -Path $heartbeatTxt -Encoding UTF8

if ($errors.Count -gt 0) { exit 2 }
if (-not $finalReady) { exit 1 }
exit 0
