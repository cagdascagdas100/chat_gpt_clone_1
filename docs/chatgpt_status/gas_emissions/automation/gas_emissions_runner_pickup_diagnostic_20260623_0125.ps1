$ErrorActionPreference = 'Continue'
$PageKey = 'gas_emissions'
$RepoRoot = Get-Location
$PageRoot = 'docs/chatgpt_status/gas_emissions'
$ReportPath = Join-Path $PageRoot 'reports/runner_pickup_diagnostic_20260623_0125.md'
$StatusPath = Join-Path $PageRoot 'status/runner_pickup_diagnostic_20260623_0125.json'
$HeartbeatPath = Join-Path $PageRoot 'heartbeat/runner_pickup_diagnostic_20260623_0125.json'
$SharedState = 'F:\chatgpt\AAYS_WORK\single_runner\state\MULTI_PAGE'
$SharedRunnerScript = 'docs/chatgpt_status/_shared/automation/RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER.ps1'
$ExpectedQueue = Join-Path $PageRoot 'queue/gas_emissions_finalizer_20260622_2300.queue.json'
$ExpectedScript = Join-Path $PageRoot 'automation/gas_emissions_single_runner_finalizer_20260622_2300.ps1'
$ExpectedStatus = Join-Path $PageRoot 'status/gas_emissions_finalizer_status_20260622_2300.json'
$ExpectedHeartbeat = Join-Path $PageRoot 'heartbeat/gas_emissions_finalizer_heartbeat_20260622_2300.json'
$ExpectedReport = Join-Path $PageRoot 'reports/gas_emissions_finalizer_result_20260622_2300.md'
New-Item -ItemType Directory -Force (Split-Path $ReportPath) | Out-Null
New-Item -ItemType Directory -Force (Split-Path $StatusPath) | Out-Null
New-Item -ItemType Directory -Force (Split-Path $HeartbeatPath) | Out-Null
function Get-ExistsInfo($Path) {
  $item = Get-Item -LiteralPath $Path -ErrorAction SilentlyContinue
  if ($item) { return @{ path=$Path; exists=$true; full_name=$item.FullName; length=$item.Length; last_write_time=$item.LastWriteTime.ToString('o') } }
  return @{ path=$Path; exists=$false; full_name=''; length=0; last_write_time='' }
}
function Read-Head($Path, $MaxChars=4000) {
  try {
    if (Test-Path -LiteralPath $Path) {
      $s = Get-Content -Raw -Encoding UTF8 -LiteralPath $Path
      if ($s.Length -gt $MaxChars) { return $s.Substring(0,$MaxChars) }
      return $s
    }
  } catch { return $_.Exception.Message }
  return ''
}
$now = Get-Date -Format o
$paths = @(
  (Get-ExistsInfo $SharedRunnerScript),
  (Get-ExistsInfo $ExpectedQueue),
  (Get-ExistsInfo $ExpectedScript),
  (Get-ExistsInfo $ExpectedStatus),
  (Get-ExistsInfo $ExpectedHeartbeat),
  (Get-ExistsInfo $ExpectedReport),
  (Get-ExistsInfo $SharedState),
  (Get-ExistsInfo (Join-Path $SharedState 'current-task.json')),
  (Get-ExistsInfo (Join-Path $SharedState 'queue')),
  (Get-ExistsInfo (Join-Path $SharedState 'history')),
  (Get-ExistsInfo (Join-Path $SharedState 'logs')),
  (Get-ExistsInfo (Join-Path $SharedState 'status'))
)
$repoSearch = @{}
foreach ($term in @('RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER','current-task','runner_tasks','single_runner','MULTI_PAGE','gas_emissions_finalizer_20260622_2300')) {
  try { $repoSearch[$term] = (& git grep -n $term -- docs/chatgpt_status 2>$null | Select-Object -First 20) -join "`n" } catch { $repoSearch[$term] = '' }
}
$sharedListing = @()
if (Test-Path -LiteralPath $SharedState) {
  $sharedListing = Get-ChildItem -LiteralPath $SharedState -Force -Recurse -ErrorAction SilentlyContinue | Select-Object -First 200 FullName, Length, LastWriteTime
}
$currentTaskText = Read-Head (Join-Path $SharedState 'current-task.json')
$heartbeatText = Read-Head $ExpectedHeartbeat
$statusText = Read-Head $ExpectedStatus
$diagnosis = 'runner_pickup_contract_unresolved'
$powerShellRequired = $true
if ((Test-Path -LiteralPath $ExpectedQueue) -and (Test-Path -LiteralPath $ExpectedScript) -and (Test-Path -LiteralPath $ExpectedHeartbeat)) {
  if ($heartbeatText -match 'runner_script_finished') { $diagnosis = 'runner_has_finished_finalizer'; $powerShellRequired = $false }
  elseif ($heartbeatText -match 'runner_script_started') { $diagnosis = 'runner_started_but_not_finished'; $powerShellRequired = $false }
  else { $diagnosis = 'queue_and_script_exist_but_runner_has_not_picked_task' }
}
$statusObj = [ordered]@{
  schema_version='aays.runner_pickup_diagnostic.v1'
  page_key=$PageKey
  status=$diagnosis
  completion_percent=89
  can_mark_100_percent=$false
  power_shell_required_for_product_patch=$false
  power_shell_required_for_runner_contract=$powerShellRequired
  shared_state=$SharedState
  shared_runner_script=$SharedRunnerScript
  expected_queue=$ExpectedQueue
  expected_script=$ExpectedScript
  expected_status=$ExpectedStatus
  expected_heartbeat=$ExpectedHeartbeat
  expected_report=$ExpectedReport
  checked_paths=$paths
  updated_at=$now
}
$statusObj | ConvertTo-Json -Depth 12 | Set-Content -Encoding UTF8 $StatusPath
$report = @()
$report += '# Gas Emissions Runner Pickup Diagnostic'
$report += ''
$report += "UPDATED_AT=$now"
$report += "STATUS=$diagnosis"
$report += 'COMPLETION_PERCENT=89'
$report += 'CAN_MARK_100_PERCENT=false'
$report += "SHARED_STATE=$SharedState"
$report += "SHARED_RUNNER_SCRIPT=$SharedRunnerScript"
$report += ''
$report += '## Checked paths'
foreach ($p in $paths) { $report += "- exists=$($p.exists) length=$($p.length) path=$($p.path) last_write=$($p.last_write_time)" }
$report += ''
$report += '## Current task head'
$report += '```json'
$report += $currentTaskText
$report += '```'
$report += ''
$report += '## Existing heartbeat head'
$report += '```json'
$report += $heartbeatText
$report += '```'
$report += ''
$report += '## Existing status head'
$report += '```json'
$report += $statusText
$report += '```'
$report += ''
$report += '## Repo search summary'
foreach ($k in $repoSearch.Keys) { $report += "### $k"; $report += '```text'; $report += $repoSearch[$k]; $report += '```' }
$report += ''
$report += '## Stop rule'
$report += 'Do not mark FINAL_READY until the finalizer status/report contain runtime polygon_join, endpoint HTTP 200, and non-empty gas popup or side-panel evidence.'
$report | Set-Content -Encoding UTF8 $ReportPath
@{ schema_version='aays.heartbeat.v1'; page_key=$PageKey; state='runner_pickup_diagnostic_written'; status=$diagnosis; updated_at=$now; report_path=$ReportPath; status_path=$StatusPath } | ConvertTo-Json -Depth 6 | Set-Content -Encoding UTF8 $HeartbeatPath
try {
  git add $ReportPath $StatusPath $HeartbeatPath
  git commit -m 'docs(gas-emissions): write runner pickup diagnostic output' | Out-Null
  git push origin HEAD | Out-Null
} catch { }
exit 0
