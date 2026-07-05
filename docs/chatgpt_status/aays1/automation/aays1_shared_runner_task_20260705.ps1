param(
  [string]$RepoRoot = $env:AAYS_REPO_ROOT,
  [string]$TaskId = $env:AAYS_TASK_ID
)
$ErrorActionPreference = 'Stop'
if ([string]::IsNullOrWhiteSpace($RepoRoot)) { $RepoRoot = (Get-Location).Path }
if ([string]::IsNullOrWhiteSpace($TaskId)) { $TaskId = 'aays1_current_20260705' }
$RepoRoot = [System.IO.Path]::GetFullPath($RepoRoot)
function D($p){ if($p -and -not(Test-Path -LiteralPath $p)){ New-Item -ItemType Directory -Force -Path $p | Out-Null } }
function W($rel,$content){ $full=Join-Path $RepoRoot ($rel -replace '/','\'); D (Split-Path -Parent $full); [System.IO.File]::WriteAllText($full,$content,[System.Text.UTF8Encoding]::new($false)) }
function J($o){ $o|ConvertTo-Json -Depth 20 }
$page='aays1'
$reportRel="docs/chatgpt_status/aays1/reports/${TaskId}_runner_output.txt"
$statusRel="docs/chatgpt_status/aays1/status/${TaskId}_completed.json"
$gateRel="docs/chatgpt_status/aays1/status/${TaskId}_gate.json"
$heartbeatRel="docs/chatgpt_status/aays1/heartbeat/${TaskId}_heartbeat.txt"
$blockers=@('missing_vision_outputs_or_manual_review_required')
$payload=[ordered]@{task_id=$TaskId;page_key=$page;updated_at=(Get-Date).ToUniversalTime().ToString('s')+'Z';queue_seen=$true;queue_started=$true;CONTINUE_RUNNER_READY=$true;final_ready=$false;fake_data=$false;blockers=$blockers;next_action='ChatGPT can add verified AI boundary outputs to the queue, then say devam et.'}
W $reportRel "AAYS1 shared runner task`nfinal_ready=false`nfake_data=false`nblockers=$($blockers -join ';')`n"
W $statusRel (J $payload)
W $gateRel (J ([ordered]@{task_id=$TaskId;page_key=$page;source_row_gate_passed=$false;ui_token_gate_passed=$false;browser_smoke_passed=$false;post_sync_ok=$false;manual_review_required=$true;fake_data=$false;blockers=$blockers}))
W $heartbeatRel "TASK_ID=$TaskId`nPAGE_KEY=$page`nSTATUS=completed_no_fake_data`nHEARTBEAT_AT=$((Get-Date).ToUniversalTime().ToString('s'))Z`n"
Write-Output "aays1_shared_task_completed final_ready=false"