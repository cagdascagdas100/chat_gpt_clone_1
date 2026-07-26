param()
$ErrorActionPreference = 'Continue'
$pageKey = 'AAYS_REAL_TOPOGRAPHY_PRODUCT'
$taskId = 'page34_runner_push_chain_probe_20260625_001'
$repoRoot = 'C:\Users\cagda\Documents\GitHub\AAYS'
$bridgeRoot = $env:AAYS_BRIDGE_ROOT
if ([string]::IsNullOrWhiteSpace($bridgeRoot)) {
  foreach ($candidate in @('F:\AAYS_GITHUB_BRIDGE_CLEAN2','D:\AAYS_GITHUB_BRIDGE_CLEAN2','C:\AAYS_GITHUB_BRIDGE_CLEAN2')) {
    if (Test-Path $candidate) { $bridgeRoot = $candidate; break }
  }
}
$reportRel = "docs/chatgpt_status/$pageKey/reports/$taskId`_report.md"
$statusRel = "docs/chatgpt_status/$pageKey/status/$taskId`_status.json"
$outputRel = "docs/chatgpt_status/$pageKey/runner_outputs/$taskId`_runner_output.txt"
$reportPath = Join-Path $repoRoot $reportRel
$statusPath = Join-Path $repoRoot $statusRel
$outputPath = Join-Path $repoRoot $outputRel
New-Item -ItemType Directory -Force -Path (Split-Path $reportPath), (Split-Path $statusPath), (Split-Path $outputPath) | Out-Null
$checks = [ordered]@{}
$checks.repo_root = $repoRoot
$checks.repo_root_exists = Test-Path $repoRoot
$checks.bridge_root = $bridgeRoot
$checks.bridge_root_exists = if ($bridgeRoot) { Test-Path $bridgeRoot } else { $false }
$checks.expected_pending_dir = if ($bridgeRoot) { Join-Path $bridgeRoot 'ai-queue\pending' } else { $null }
$checks.expected_pending_dir_exists = if ($checks.expected_pending_dir) { Test-Path $checks.expected_pending_dir } else { $false }
$checks.repo_queue_task = Join-Path $repoRoot "docs\chatgpt_status\$pageKey\queue\$taskId.task.json"
$checks.repo_queue_task_exists = Test-Path $checks.repo_queue_task
$checks.f_pending_task = if ($bridgeRoot) { Join-Path $bridgeRoot "ai-queue\pending\$taskId.task.json" } else { $null }
$checks.f_pending_task_exists = if ($checks.f_pending_task) { Test-Path $checks.f_pending_task } else { $false }
Push-Location $repoRoot
$checks.git_remote = (git remote -v 2>&1) -join "`n"
$checks.git_branch = (git branch --show-current 2>&1) -join "`n"
$checks.git_status_before = (git status --short 2>&1) -join "`n"
Pop-Location
$blockers = New-Object System.Collections.Generic.List[string]
if (-not $checks.repo_root_exists) { $blockers.Add('wrong_root: repo root missing') }
if (-not $checks.bridge_root_exists) { $blockers.Add('wrong_root: bridge root missing') }
if (-not $checks.expected_pending_dir_exists) { $blockers.Add('path_mismatch: F bridge ai-queue pending missing') }
if (-not $checks.f_pending_task_exists) { $blockers.Add('runner_pickup_not_proven: task not present in F ai-queue pending') }
if ($checks.git_branch -ne 'main') { $blockers.Add('wrong_branch: local branch is not main') }
if (($checks.git_remote -notmatch 'cagdascagdas100/chat_gpt_clone_1') -and ($checks.git_remote -notmatch 'chat_gpt_clone_1.git')) { $blockers.Add('wrong_repo: local remote does not point to cagdascagdas100/chat_gpt_clone_1') }
$now = Get-Date -Format o
$finalReady = $false
$completion = 75
$report = @"
# AAYS page34 runner push chain probe

- timestamp: $now
- task_id: $taskId
- page_key: $pageKey
- repo_root: $repoRoot
- bridge_root: $bridgeRoot
- expected_pending_dir: $($checks.expected_pending_dir)
- repo_queue_task_exists: $($checks.repo_queue_task_exists)
- f_pending_task_exists: $($checks.f_pending_task_exists)
- git_branch: $($checks.git_branch)

## Git remote
````text
$($checks.git_remote)
````

## Git status before
````text
$($checks.git_status_before)
````

## Blockers
$((if ($blockers.Count -eq 0) { '- none' } else { ($blockers | ForEach-Object { "- $_" }) -join "`n" }))

## Result
- runner_pickup: $(if ($checks.f_pending_task_exists) { 'proven' } else { 'not_proven' })
- runner_push: local_probe_created_pending_git_push
- completion_percent: $completion
- final_ready: $finalReady
"@
Set-Content -LiteralPath $reportPath -Value $report -Encoding UTF8
$status = [ordered]@{
  task_id=$taskId; page_key=$pageKey; timestamp=$now; completion_percent=$completion; final_ready=$finalReady;
  runner_pickup= if ($checks.f_pending_task_exists) { 'proven' } else { 'not_proven' };
  runner_push='local_probe_created_pending_git_push'; blockers=@($blockers); checks=$checks
} | ConvertTo-Json -Depth 8
Set-Content -LiteralPath $statusPath -Value $status -Encoding UTF8
Set-Content -LiteralPath $outputPath -Value "AAYS_RUNNER_PUSH_CHAIN_PROBE_DONE task_id=$taskId timestamp=$now" -Encoding UTF8
Push-Location $repoRoot
try {
  git add -- $reportRel $statusRel $outputRel | Out-Null
  git commit -m "AAYS page34 runner push chain probe result" | Out-Null
  git push origin main | Out-Null
} catch {
  Add-Content -LiteralPath $outputPath -Value "PUSH_FAILED: $($_.Exception.Message)"
}
Pop-Location
