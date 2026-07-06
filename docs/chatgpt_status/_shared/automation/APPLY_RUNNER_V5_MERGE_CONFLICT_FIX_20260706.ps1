[CmdletBinding()]
param(
  [string]$RepoRoot = "C:\AAYS_WT\AAYS_REPAIR_20260706_1738"
)

$ErrorActionPreference = "Stop"

$runnerPath = Join-Path $RepoRoot "docs\chatgpt_status\_shared\automation\RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_V5_20260706.ps1"
if (-not (Test-Path -LiteralPath $runnerPath)) {
  throw "Runner V5 script not found: $runnerPath"
}

$content = Get-Content -Raw -LiteralPath $runnerPath
if ($content -notmatch '<<<<<<< HEAD' -or $content -notmatch '=======' -or $content -notmatch '>>>>>>>') {
  Write-Output "NO_CONFLICT_MARKERS_FOUND path=$runnerPath"
  exit 0
}

$conflictPattern = '(?s)<<<<<<< HEAD\r?\n\s*\$scriptBlockers = @\(Get-ScriptBlockers -ScriptOutput \$scriptOutput\).*?continue\r?\n\s*}\r?\n=======\r?\n>>>>>>> [0-9a-f]+\r?\n'
$replacement = @'
      $null = Write-TaskEvidence -Task $task -Status "failed" -Blockers @("automation_script_failed") -Errors @($scriptOutput) -ScriptOutput $scriptOutput -QueueStarted $true -CleanWorktree $true
      $skipped.Add([pscustomobject]@{ page_key = $task.page_key; task_id = $task.task_id; status = "failed"; blockers = @("automation_script_failed") })
      $blockers.Add("automation_script_failed")
      continue
'@

$newContent = [regex]::Replace($content, $conflictPattern, $replacement)
if ($newContent -eq $content) {
  throw "Conflict marker pattern was not replaced. Manual inspection required."
}

Set-Content -LiteralPath $runnerPath -Value $newContent -Encoding UTF8

$verify = Get-Content -Raw -LiteralPath $runnerPath
if ($verify -match '<<<<<<<|=======|>>>>>>>') {
  throw "Patch verification failed: merge conflict markers still present."
}
if ($verify -match 'Get-ScriptBlockers') {
  throw "Patch verification failed: unresolved Get-ScriptBlockers reference remains."
}

Write-Output "PATCH_APPLIED runner_v5_merge_conflict_removed=true path=$runnerPath"
