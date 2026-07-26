$ErrorActionPreference = 'Stop'
$repoRoot = 'C:\Users\cagda\Documents\GitHub\AAYS'
$pageKey = 'AAYS_REAL_TOPOGRAPHY_PRODUCT'
$base = Join-Path $repoRoot "docs\chatgpt_status\$pageKey"
$reportDir = Join-Path $base 'reports'
$statusDir = Join-Path $base 'status'
$heartbeatDir = Join-Path $base 'heartbeat'
$runnerOutDir = Join-Path $base 'runner_outputs'
New-Item -ItemType Directory -Force -Path $reportDir,$statusDir,$heartbeatDir,$runnerOutDir | Out-Null
$bridgeRoot = if ($env:AAYS_BRIDGE_ROOT) { $env:AAYS_BRIDGE_ROOT } elseif (Test-Path 'F:\AAYS_GITHUB_BRIDGE_CLEAN2') { 'F:\AAYS_GITHUB_BRIDGE_CLEAN2' } elseif (Test-Path 'D:\AAYS_GITHUB_BRIDGE_CLEAN2') { 'D:\AAYS_GITHUB_BRIDGE_CLEAN2' } else { 'C:\AAYS_GITHUB_BRIDGE_CLEAN2' }
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$report = Join-Path $reportDir "bridge_root_contract_probe_$stamp.md"
$status = Join-Path $statusDir "bridge_root_contract_probe_$stamp.status.txt"
$heartbeat = Join-Path $heartbeatDir "bridge_root_contract_probe_$stamp.heartbeat.txt"
$runnerOut = Join-Path $runnerOutDir "bridge_root_contract_probe_$stamp.runner_output.txt"
$lines = @(
  '# Bridge Root Contract Probe',
  "page_key=$pageKey",
  "repo_root=$repoRoot",
  "bridge_root=$bridgeRoot",
  "bridge_exists=$(Test-Path $bridgeRoot)",
  "pending_exists=$(Test-Path (Join-Path $bridgeRoot 'ai-queue\pending'))",
  "status=probe_completed_no_final_ready"
)
$lines | Set-Content -Encoding UTF8 $report
$lines | Set-Content -Encoding UTF8 $runnerOut
@('status=probe_completed_no_final_ready', 'final_ready=false', 'percent=93') | Set-Content -Encoding UTF8 $status
@("heartbeat_utc=$((Get-Date).ToUniversalTime().ToString('o'))", "page_key=$pageKey", "bridge_root=$bridgeRoot") | Set-Content -Encoding UTF8 $heartbeat
Set-Location $repoRoot
git add "docs/chatgpt_status/$pageKey/reports" "docs/chatgpt_status/$pageKey/status" "docs/chatgpt_status/$pageKey/heartbeat" "docs/chatgpt_status/$pageKey/runner_outputs"
git commit -m "Add bridge root contract probe evidence for $pageKey" 2>$null
git push origin main
