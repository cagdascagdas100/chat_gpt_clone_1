$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$repo = 'C:\Users\cagda\Documents\GitHub\chat_gpt_clone_1'
$scriptRel = 'docs/chatgpt_status/aays1/automation/aays1_fg100_runner_contract_blocker_20260623_008.ps1'
$reportRel = 'docs/chatgpt_status/aays1/reports/aays1_local_runner_start_20260624.txt'
$heartbeatRel = 'docs/chatgpt_status/aays1/heartbeat/aays1_local_runner_start_20260624_heartbeat.txt'

if (-not (Test-Path $repo)) {
  throw "Repo path not found: $repo"
}

Set-Location $repo
New-Item -ItemType Directory -Force -Path (Split-Path $reportRel) | Out-Null
New-Item -ItemType Directory -Force -Path (Split-Path $heartbeatRel) | Out-Null

"START_TIME=$(Get-Date -Format o)" | Out-File $reportRel -Encoding utf8
"PWD=$(Get-Location)" | Out-File $reportRel -Append -Encoding utf8
"BRANCH_BEFORE=$(git branch --show-current)" | Out-File $reportRel -Append -Encoding utf8

git pull | Out-File $reportRel -Append -Encoding utf8

if (-not (Test-Path $scriptRel)) {
  "SCRIPT_MISSING=$scriptRel" | Out-File $reportRel -Append -Encoding utf8
  throw "Script missing: $scriptRel"
}

"RUN_SCRIPT=$scriptRel" | Out-File $reportRel -Append -Encoding utf8
powershell -ExecutionPolicy Bypass -File $scriptRel *>&1 | Out-File $reportRel -Append -Encoding utf8

"HEARTBEAT_TIME=$(Get-Date -Format o)" | Out-File $heartbeatRel -Encoding utf8
"STATUS=LOCAL_RUNNER_STARTER_EXECUTED" | Out-File $heartbeatRel -Append -Encoding utf8
"EXPECTED_OUTPUT=docs/chatgpt_status/aays1/reports/aays1_fg100_runner_contract_blocker_20260623_008_runner_output.txt" | Out-File $heartbeatRel -Append -Encoding utf8
"EXPECTED_HEARTBEAT=docs/chatgpt_status/aays1/heartbeat/aays1_fg100_runner_contract_blocker_20260623_008_heartbeat.txt" | Out-File $heartbeatRel -Append -Encoding utf8

"GIT_STATUS_AFTER:" | Out-File $reportRel -Append -Encoding utf8
git status --short | Out-File $reportRel -Append -Encoding utf8

git add docs/chatgpt_status/aays1/reports docs/chatgpt_status/aays1/heartbeat
try {
  git commit -m 'run aays1 local shared runner task and publish evidence' | Out-File $reportRel -Append -Encoding utf8
} catch {
  "COMMIT_SKIPPED_OR_FAILED=$($_.Exception.Message)" | Out-File $reportRel -Append -Encoding utf8
}

git push | Out-File $reportRel -Append -Encoding utf8
"END_TIME=$(Get-Date -Format o)" | Out-File $reportRel -Append -Encoding utf8
