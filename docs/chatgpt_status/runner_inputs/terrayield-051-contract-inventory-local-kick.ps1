$ErrorActionPreference = "Continue"
$repo = "C:\Users\cagda\Documents\GitHub\AAYS"
$bridge = "C:\AAYS_GITHUB_BRIDGE_CLEAN2"
$queue = Join-Path $bridge "ai-queue"
$runner = Join-Path $bridge "ai-task-scripts\portable_queue_runner.ps1"
$froot = "F:\AAYS_GITHUB_WORK\terrayield-051-contract-inventory"
$outDir = Join-Path $repo "docs\chatgpt_status\runner_outputs"
$txt = Join-Path $outDir "runner_contract_inventory_for_051_latest.txt"
$json = Join-Path $outDir "runner_contract_inventory_for_051_latest.json"
$latest = Join-Path $outDir "latest_output.json"

New-Item -ItemType Directory -Force -Path $outDir,$froot | Out-Null
Set-Location $repo

"=== RUNNER CONTRACT INVENTORY 051 $(Get-Date -Format o) ===" | Set-Content -Encoding UTF8 $txt
"repo=$repo" | Add-Content $txt
"bridge=$bridge" | Add-Content $txt
"queue=$queue" | Add-Content $txt
"runner=$runner" | Add-Content $txt
"froot=$froot" | Add-Content $txt

"=== GIT SYNC ===" | Add-Content $txt
git checkout main 2>&1 | Add-Content $txt
git pull --rebase origin main 2>&1 | Add-Content $txt

"=== PATH CHECK ===" | Add-Content $txt
@(
  "repo_exists=$(Test-Path $repo)",
  "bridge_exists=$(Test-Path $bridge)",
  "queue_exists=$(Test-Path $queue)",
  "runner_exists=$(Test-Path $runner)",
  "froot_exists=$(Test-Path $froot)",
  "current_task_exists=$(Test-Path (Join-Path $repo 'docs\chatgpt_status\current-task.txt'))",
  "latest_output_exists=$(Test-Path $latest)"
) | Add-Content $txt

"=== RUNNER PROCESS SNAPSHOT BEFORE ===" | Add-Content $txt
$procs = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match "portable_queue_runner.ps1|AAYS_GITHUB_BRIDGE_CLEAN2|ai-queue" } | Select-Object ProcessId,CommandLine
if ($procs) { $procs | Format-List | Out-String | Add-Content $txt } else { "NO_MATCHING_RUNNER_PROCESS_FOUND" | Add-Content $txt }

"=== QUEUE SNAPSHOT ===" | Add-Content $txt
if (Test-Path $queue) {
  Get-ChildItem $queue -Force -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 30 Name,Length,LastWriteTime | Format-Table -AutoSize | Out-String | Add-Content $txt
} else {
  "QUEUE_PATH_MISSING" | Add-Content $txt
}

$runnerAlreadyRunning = [bool]$procs
if (-not $runnerAlreadyRunning -and (Test-Path $runner)) {
  "STARTING_SINGLE_CANONICAL_RUNNER" | Add-Content $txt
  Start-Process powershell -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$runner`""
  Start-Sleep -Seconds 10
} else {
  "RUNNER_START_SKIPPED runnerAlreadyRunning=$runnerAlreadyRunning runnerExists=$(Test-Path $runner)" | Add-Content $txt
}

"=== RUNNER PROCESS SNAPSHOT AFTER ===" | Add-Content $txt
$procsAfter = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match "portable_queue_runner.ps1|AAYS_GITHUB_BRIDGE_CLEAN2|ai-queue" } | Select-Object ProcessId,CommandLine
if ($procsAfter) { $procsAfter | Format-List | Out-String | Add-Content $txt } else { "NO_MATCHING_RUNNER_PROCESS_FOUND_AFTER" | Add-Content $txt }

[ordered]@{
  task_id="runner-contract-inventory-for-terrayield-051"
  parent_task_id="terrayield-051-london-only-pilot"
  status="contract_inventory_written_by_local_powershell"
  overall_progress_percent=30
  repo=$repo
  bridge=$bridge
  queue=$queue
  runner=$runner
  froot=$froot
  repo_exists=(Test-Path $repo)
  bridge_exists=(Test-Path $bridge)
  queue_exists=(Test-Path $queue)
  runner_exists=(Test-Path $runner)
  runner_process_seen_before=$runnerAlreadyRunning
  runner_process_seen_after=[bool]$procsAfter
  product_changes_run=$false
  powershell_output_copied_to_github=$true
  timestamp=(Get-Date -Format o)
} | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 $json

[ordered]@{
  task_id="runner-contract-inventory-for-terrayield-051"
  parent_task_id="terrayield-051-london-only-pilot"
  status="contract_inventory_available"
  overall_progress_percent=30
  phase="runner_contract_inventory_written_to_github"
  next_chatgpt_action="read_contract_inventory_and_resume_terrayield_051_london_only_pilot"
  manual_powershell_required_now=$false
  timestamp=(Get-Date -Format o)
} | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 $latest

git add docs/chatgpt_status/runner_outputs/runner_contract_inventory_for_051_latest.txt docs/chatgpt_status/runner_outputs/runner_contract_inventory_for_051_latest.json docs/chatgpt_status/runner_outputs/latest_output.json
git commit -m "Add runner contract inventory for TerraYield 051"
git push origin main
