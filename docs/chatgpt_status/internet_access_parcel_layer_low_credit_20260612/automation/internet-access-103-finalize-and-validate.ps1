$PageKey='internet_access_parcel_layer_low_credit_20260612'
$TaskId='internet-access-103-finalize-and-validate'
$Root=(Resolve-Path '.').Path
$Dir=Join-Path $Root "docs/chatgpt_status/$PageKey/reports"
New-Item -ItemType Directory -Force $Dir | Out-Null
$Report=Join-Path $Dir "$TaskId.txt"
@"
task_id=$TaskId
page_key=$PageKey
status=VALIDATION_REQUESTED
completion_percent=60
manual_stdout_required=false
expected_next_status=FINAL_READY_OR_MISSING_ARTIFACT_REPORT
"@ | Set-Content $Report -Encoding UTF8
exit 0
