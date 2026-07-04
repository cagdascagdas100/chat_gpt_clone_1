param(
  [string]$RepoRoot = $env:AAYS_REPO_ROOT,
  [string]$TaskId = $env:AAYS_TASK_ID
)
$ErrorActionPreference = 'Stop'
if([string]::IsNullOrWhiteSpace($RepoRoot)){ $RepoRoot = (Get-Location).Path }
if([string]::IsNullOrWhiteSpace($TaskId)){ $TaskId = '000_shared_runner_watchdog_20260704' }
function D($p){ if($p -and !(Test-Path -LiteralPath $p)){ New-Item -ItemType Directory -Force -Path $p | Out-Null } }
function W($p,$c){ D (Split-Path -Parent $p); [IO.File]::WriteAllText($p,$c,[Text.UTF8Encoding]::new($false)) }
function J($o){ $o|ConvertTo-Json -Depth 20 }
function N(){ (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ') }
Set-Location -LiteralPath $RepoRoot
$canonical = 'docs/chatgpt_status/_shared/automation/RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER.ps1'
$v2 = 'docs/chatgpt_status/_shared/automation/RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_V2_20260704.ps1'
$locked = 'docs/chatgpt_status/_shared/automation/RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_V2_LOCKED_20260704.ps1'
$topoQueue = 'docs/chatgpt_status/topography/queue/000_topography_priority_shared_runner_task_20260704.json'
$topoDone = 'docs/chatgpt_status/topography/status/000_topography_priority_shared_runner_task_20260704_completed.json'
$gitHead = ''
try { $gitHead = (& git rev-parse HEAD 2>$null) } catch {}
$payload = [ordered]@{
  task_id = $TaskId
  page_key = '_shared'
  checked_at = N
  repo_root = $RepoRoot
  git_head = $gitHead
  canonical_exists = Test-Path -LiteralPath $canonical
  v2_exists = Test-Path -LiteralPath $v2
  locked_launcher_exists = Test-Path -LiteralPath $locked
  topography_priority_queue_exists = Test-Path -LiteralPath $topoQueue
  topography_completed_exists = Test-Path -LiteralPath $topoDone
  final_ready = $false
  fake_data = $false
  blocker = if(Test-Path -LiteralPath $topoDone){'NONE'}else{'TOPOGRAPHY_QUEUE_NOT_COMPLETED_YET'}
}
W "docs/chatgpt_status/_shared/status/${TaskId}_completed.json" (J $payload)
W "docs/chatgpt_status/_shared/reports/${TaskId}_runner_output.txt" ((J $payload) + "`n")
W "docs/chatgpt_status/_shared/heartbeat/${TaskId}_heartbeat.txt" "TASK_ID=$TaskId`nSTATUS=completed`nHEARTBEAT_AT=$(N)`n"
W "docs/chatgpt_status/_shared/status/${TaskId}_gate.json" (J ([ordered]@{source_row_gate_passed=$false;ui_token_gate_passed=$false;browser_smoke_passed=$false;post_sync_ok=$false;manual_review_required=$true;fake_data=$false}))
Write-Output ('shared_runner_watchdog_completed topo_done=' + $payload.topography_completed_exists)
