$ErrorActionPreference = 'Continue'
$PageKey = 'AAYS_REAL_TOPOGRAPHY_PRODUCT'
$TaskId = 'topography_single_runner_contract_recovery_20260623T010000Z'
$Root = (Resolve-Path '.').Path
$ReportDir = Join-Path $Root "docs/chatgpt_status/$PageKey/reports"
$StatusDir = Join-Path $Root "docs/chatgpt_status/$PageKey/status"
New-Item -ItemType Directory -Force -Path $ReportDir | Out-Null
New-Item -ItemType Directory -Force -Path $StatusDir | Out-Null
$Report = Join-Path $ReportDir "${TaskId}_local_runner_recheck_report.txt"
$Status = Join-Path $StatusDir "${TaskId}_local_runner_recheck.status.txt"
$Runner = Join-Path $Root 'docs/chatgpt_status/_shared/automation/RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER.ps1'
$ExpectedAutomation = Join-Path $Root "docs/chatgpt_status/$PageKey/automation/${TaskId}_v6.ps1"
Set-Content -Path $Report -Value "LOCAL_RUNNER_RECHECK_STARTED=$(Get-Date -Format o)"
Add-Content -Path $Report -Value "PAGE_KEY=$PageKey"
Add-Content -Path $Report -Value "TASK_ID=$TaskId"
Add-Content -Path $Report -Value "ROOT=$Root"
Add-Content -Path $Report -Value "RUNNER_SCRIPT=$Runner"
Add-Content -Path $Report -Value "EXPECTED_AUTOMATION=$ExpectedAutomation"
Add-Content -Path $Report -Value "SEPARATE_RUNNER_STARTED=false"
Add-Content -Path $Report -Value "DB_WRITE=false"
Add-Content -Path $Report -Value "MIGRATION=false"
Add-Content -Path $Report -Value "PRODUCTION_DEPLOY=false"
if (Test-Path $ExpectedAutomation) {
  Add-Content -Path $Report -Value "EXPECTED_AUTOMATION_FOUND=true"
} else {
  Add-Content -Path $Report -Value "EXPECTED_AUTOMATION_FOUND=false"
}
if (Test-Path $Runner) {
  Add-Content -Path $Report -Value "RUNNER_SCRIPT_FOUND=true"
  Add-Content -Path $Report -Value "RUNNER_CALL_STARTED=$(Get-Date -Format o)"
  powershell -ExecutionPolicy Bypass -File $Runner *>> $Report
  Add-Content -Path $Report -Value "RUNNER_CALL_FINISHED=$(Get-Date -Format o)"
} else {
  Add-Content -Path $Report -Value "RUNNER_SCRIPT_FOUND=false"
  Add-Content -Path $Report -Value "BLOCKER=shared_runner_script_missing_on_local_worktree"
}
Set-Content -Path $Status -Value "LOCAL_RUNNER_RECHECK_STATUS=WRITTEN"
Add-Content -Path $Status -Value "PAGE_KEY=$PageKey"
Add-Content -Path $Status -Value "TASK_ID=$TaskId"
Add-Content -Path $Status -Value "REPORT=$($Report.Replace($Root + '\',''))"
Add-Content -Path $Status -Value "FINISHED_AT=$(Get-Date -Format o)"
git add "docs/chatgpt_status/$PageKey" | Out-Null
git commit -m "AAYS topography local runner recheck evidence" | Out-Null
git push | Out-Null
