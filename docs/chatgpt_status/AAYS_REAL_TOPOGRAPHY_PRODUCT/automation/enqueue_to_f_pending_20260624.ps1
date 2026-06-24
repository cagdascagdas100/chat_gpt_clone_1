$ErrorActionPreference = 'Stop'
$pageKey = 'AAYS_REAL_TOPOGRAPHY_PRODUCT'
$taskId = 'topography_single_runner_contract_recovery_20260623T010000Z'
$repoRoot = 'C:\Users\cagda\Documents\GitHub\AAYS'
$bridgeRoot = if ($env:AAYS_BRIDGE_ROOT) { $env:AAYS_BRIDGE_ROOT } else { 'F:\AAYS_GITHUB_BRIDGE_CLEAN2' }
$pageRoot = Join-Path $repoRoot "docs\chatgpt_status\$pageKey"
$queueDir = Join-Path $pageRoot 'queue'
$reportsDir = Join-Path $pageRoot 'reports'
$statusDir = Join-Path $pageRoot 'status'
$pendingDir = Join-Path $bridgeRoot 'ai-queue\pending'
New-Item -ItemType Directory -Force -Path $queueDir,$reportsDir,$statusDir,$pendingDir | Out-Null
$scriptPath = Join-Path $pageRoot 'automation\topography_single_runner_contract_recovery_20260623T010000Z_v6.ps1'
$taskJson = Join-Path $queueDir "$taskId.task.json"
$pendingJson = Join-Path $pendingDir "$taskId.task.json"
$resultPath = Join-Path $bridgeRoot "ai-results\$pageKey\$taskId.result.json"
$repoResultPath = Join-Path $pageRoot "runner_outputs\$taskId.v6_runner_output.txt"
$task = [ordered]@{
 task_id = $taskId
 page_key = $pageKey
 script_path = $scriptPath
 result_path = $resultPath
 repo_result_path = $repoResultPath
 status = 'pending'
 priority = 100
 db_write = $false
 ddl = $false
 migration = $false
 production_deploy = $false
 fake_data = $false
}
$task | ConvertTo-Json -Depth 6 | Set-Content -Encoding UTF8 $taskJson
Copy-Item $taskJson $pendingJson -Force
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
"pending_task_json=$pendingJson`nrepo_task_json=$taskJson`nstatus=pending_synced`nfinal_ready=false`npercent=93" | Set-Content -Encoding UTF8 (Join-Path $reportsDir "pending_json_synced_$stamp.md")
"status=pending_synced`nfinal_ready=false`npercent=93" | Set-Content -Encoding UTF8 (Join-Path $statusDir "pending_json_synced_$stamp.status.txt")
Write-Host 'AAYS_PENDING_JSON_SYNCED'
Write-Host $pendingJson
