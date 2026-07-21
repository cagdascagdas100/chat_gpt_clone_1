param(
  [string]$RepoRoot = $env:AAYS_REPO_ROOT,
  [string]$SlotId = $env:AAYS_SLOT_ID,
  [string]$TargetBranch = $env:AAYS_TARGET_BRANCH
)
$ErrorActionPreference = 'Stop'
if ($SlotId -ne 'security_public_safety_2') { throw "WRONG_SLOT:$SlotId" }
if ($TargetBranch -ne 'codex/aays-single-runner-v5-20260706') { throw "WRONG_BRANCH:$TargetBranch" }
if (-not $RepoRoot) { throw 'AAYS_REPO_ROOT_REQUIRED' }
$sharedRoot = Join-Path $RepoRoot 'docs/chatgpt_status/_shared/slots_18/security_public_safety_2'
$currentTask = Join-Path $sharedRoot 'current_task_latest.json'
$statusPath = Join-Path $sharedRoot 'status_latest.json'
$ownershipPath = Join-Path $sharedRoot 'ownership_latest.json'
foreach ($path in @($currentTask,$statusPath,$ownershipPath)) { if (-not (Test-Path $path)) { throw "AUTHORITATIVE_FILE_NOT_FOUND:$path" } }
$task = Get-Content $currentTask -Raw | ConvertFrom-Json
$status = Get-Content $statusPath -Raw | ConvertFrom-Json
$ownership = Get-Content $ownershipPath -Raw | ConvertFrom-Json
if ($task.slot_id -ne $SlotId -or $status.slot_id -ne $SlotId -or $ownership.slot_id -ne $SlotId) { throw 'WRONG_SLOT_CONTRACT' }
if ($task.allowed_paths -notcontains 'england_map_web/data/aays_18_slots/security_public_safety_2') { throw 'WEB_PATH_NOT_ALLOWED' }
if ($task.direct_push_forbidden -ne $true) { throw 'DIRECT_PUSH_GUARD_MISSING' }
[ordered]@{
  slot_id=$SlotId
  workstream_id='AAYS_18_SLOT_SAFE_PARALLEL_V1'
  shared_root='docs/chatgpt_status/_shared/slots_18/security_public_safety_2'
  web_root='england_map_web/data/aays_18_slots/security_public_safety_2'
  status_state=$status.state
  ownership_state=$ownership.state
  current_task_state=$task.state
  direct_push_forbidden=$task.direct_push_forbidden
  contract_status='PASS'
  final_ready=$false
} | ConvertTo-Json -Depth 6
