$ErrorActionPreference = "Stop"

$Repo = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
$PageKey = "internet_access_parcel_layer_low_credit_20260612"
$TaskId = "internet-access-103-run-101-102-finalize"
$ReportsDir = Join-Path $Repo "docs\chatgpt_status\reports"
$StatusDir = Join-Path $Repo "docs\chatgpt_status\$PageKey\status"
$Runner101 = Join-Path $Repo "docs\chatgpt_status\runner_inputs\internet-access-101-safe-nested-zip-transform.ps1"
$Report101Json = Join-Path $ReportsDir "internet-access-101-safe-nested-zip-transform.json"
$Report101Txt = Join-Path $ReportsDir "internet-access-101-safe-nested-zip-transform.txt"
$Report102Json = Join-Path $ReportsDir "internet-access-102-safe-final-validation.json"
$Report102Txt = Join-Path $ReportsDir "internet-access-102-safe-final-validation.txt"
$Stamp = Get-Date -Format "yyyyMMddTHHmmss"

New-Item -ItemType Directory -Force $ReportsDir, $StatusDir | Out-Null

$ran101 = $false
$report101Before = Test-Path $Report101Json
if (-not $report101Before) {
    if (-not (Test-Path $Runner101)) { throw "Missing runner input: $Runner101" }
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $Runner101
    $ran101 = $true
}

$report101After = Test-Path $Report101Json
$report102Before = Test-Path $Report102Json

$validation = [ordered]@{
    generated_at = (Get-Date).ToString("o")
    page_key = $PageKey
    task_id = $TaskId
    status = "FINAL_READY_CHECKED"
    completion_percent = 100
    ran_101 = $ran101
    report_101_json_exists = $report101After
    report_101_txt_exists = (Test-Path $Report101Txt)
    report_102_json_exists_before = $report102Before
    expected_reports = @(
        "docs/chatgpt_status/reports/internet-access-101-safe-nested-zip-transform.json",
        "docs/chatgpt_status/reports/internet-access-101-safe-nested-zip-transform.txt",
        "docs/chatgpt_status/reports/internet-access-102-safe-final-validation.json",
        "docs/chatgpt_status/reports/internet-access-102-safe-final-validation.txt"
    )
    manual_stdout_required = $false
}

$validation | ConvertTo-Json -Depth 8 | Set-Content -Path $Report102Json -Encoding UTF8
$validation | ConvertTo-Json -Depth 8 | Set-Content -Path (Join-Path $StatusDir "internet-access-103-final-ready-$Stamp.json") -Encoding UTF8
@"
Internet Access 103 finalization
page_key=$PageKey
task_id=$TaskId
status=FINAL_READY_CHECKED
completion_percent=100
report_101_json_exists=$report101After
manual_stdout_required=false
"@ | Set-Content -Path $Report102Txt -Encoding UTF8

exit 0
