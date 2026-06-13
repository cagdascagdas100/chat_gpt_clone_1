$ErrorActionPreference = 'Stop'
$RepoRoot = 'F:\chatgpt\AAYS_WORKTREES\aays-runner-v17-icon-work-20260603-232706'
$Branch = 'aays-runner-v17-icon-work-20260603-232706'
$PageKey = 'AAYS_REAL_TOPOGRAPHY_PRODUCT'
$Ts = Get-Date -Format 'yyyyMMdd_HHmmss'
$ReportRel = "docs/chatgpt_status/$PageKey/reports/runner_self_test_${Ts}.md"
$StatusRel = "docs/chatgpt_status/$PageKey/status/runner_self_test_status_${Ts}.md"
$ReportPath = Join-Path $RepoRoot ($ReportRel -replace '/', '\')
$StatusPath = Join-Path $RepoRoot ($StatusRel -replace '/', '\')
New-Item -ItemType Directory -Force -Path (Split-Path $ReportPath) | Out-Null
New-Item -ItemType Directory -Force -Path (Split-Path $StatusPath) | Out-Null
$Now = Get-Date -Format o
@"
# Runner self test

status: RUNNER_SELF_TEST_OK
page_key: $PageKey
branch: $Branch
timestamp: $Now
runner_pid: $PID
repo_root: $RepoRoot

Result: This file was created by the local single runner/poller executing a queued automation artifact.
"@ | Set-Content -Encoding UTF8 -Path $ReportPath
@"
status: RUNNER_SELF_TEST_OK
completion_percent: 1
timestamp: $Now
report: $ReportRel
"@ | Set-Content -Encoding UTF8 -Path $StatusPath
Set-Location $RepoRoot
git add $ReportRel $StatusRel
git commit -m "Runner self-test output $Ts"
git push origin HEAD:$Branch
