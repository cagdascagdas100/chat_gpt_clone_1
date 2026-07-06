[CmdletBinding()]
param(
  [string]$RepoRoot = "C:\AAYS_WT\AAYS_REPAIR_20260706_1738",
  [string]$RunnerPath = "docs\chatgpt_status\_shared\automation\RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_V5_20260706.ps1"
)

$ErrorActionPreference = "Stop"
Set-Location $RepoRoot

$fullPath = Join-Path $RepoRoot $RunnerPath
if (!(Test-Path -LiteralPath $fullPath)) {
  throw "Runner file not found: $fullPath"
}

$text = Get-Content -Raw -LiteralPath $fullPath

# Repair the known merge-conflict fragment inside the nonzero exit-code branch.
$pattern = '(?s)<<<<<<< HEAD\s*\r?\n\s*\$scriptBlockers = @\(Get-ScriptBlockers -ScriptOutput \$scriptOutput\).*?continue\s*\r?\n\s*}\s*\r?\n=======\s*\r?\n>>>>>>> [0-9a-f]+\s*\r?\n\s*\$null = Write-TaskEvidence -Task \$task -Status "failed"'
$replacement = @'
$scriptBlockers = @(Get-ScriptBlockers -ScriptOutput $scriptOutput)
      if ($exitCode -eq 2 -or $scriptBlockers.Count -gt 0) {
        if ($scriptBlockers.Count -eq 0) { $scriptBlockers = @("automation_script_reported_blocker") }
        $null = Write-TaskEvidence -Task $task -Status "blocked" -Blockers $scriptBlockers -Errors @($scriptOutput) -ScriptOutput $scriptOutput -QueueStarted $true -CleanWorktree $true
        $skipped.Add([pscustomobject]@{ page_key = $task.page_key; task_id = $task.task_id; status = "blocked"; blockers = $scriptBlockers })
        foreach ($scriptBlocker in $scriptBlockers) { $blockers.Add($scriptBlocker) }
        continue
      }
      $null = Write-TaskEvidence -Task $task -Status "failed"
'@
$text = [regex]::Replace($text, $pattern, $replacement)

# Remove any remaining raw conflict marker lines without altering normal code.
$lines = $text -split "`r?`n"
$cleaned = New-Object System.Collections.Generic.List[string]
foreach ($line in $lines) {
  if ($line -match '^<<<<<<< ' -or $line -match '^=======\s*$' -or $line -match '^>>>>>>> ') { continue }
  $cleaned.Add($line)
}
Set-Content -LiteralPath $fullPath -Value ($cleaned -join "`r`n") -Encoding UTF8

$remaining = Select-String -LiteralPath $fullPath -Pattern '<<<<<<<|=======|>>>>>>>' -SimpleMatch -ErrorAction SilentlyContinue
if ($remaining) {
  throw "Conflict markers still remain in runner file."
}

Write-Output "REPAIRED_RUNNER_CONFLICT_MARKERS=true"
Write-Output "REPAIRED_FILE=$fullPath"
