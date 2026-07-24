[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)]
  [string]$RepoRoot
)

$ErrorActionPreference = "Stop"
$slotRoot = Join-Path $RepoRoot "docs\chatgpt_status\_shared\slots"
$manifest = Get-Content -LiteralPath (Join-Path $slotRoot "manifest_latest.json") -Raw | ConvertFrom-Json
$expected = @("ready_to_sell", "gas_emissions", "height_difference", "security_public_safety", "parcel_label")
$actual = @($manifest.slots | ForEach-Object { $_.slot_id })
if ($manifest.workstream_id -ne "AAYS_5_SLOT_SAFE_PARALLEL_V1") { throw "WORKSTREAM_ID_MISMATCH" }
if ($actual.Count -ne 5 -or (@($actual | Select-Object -Unique)).Count -ne 5) { throw "SLOT_ID_UNIQUENESS_FAILED" }
foreach ($slotId in $expected) {
  if ($actual -notcontains $slotId) { throw "SLOT_MISSING: $slotId" }
  $dir = Join-Path $slotRoot $slotId
  $ownership = Get-Content -LiteralPath (Join-Path $dir "ownership_latest.json") -Raw | ConvertFrom-Json
  $checkpoint = Get-Content -LiteralPath (Join-Path $dir "checkpoint_latest.json") -Raw | ConvertFrom-Json
  $heartbeat = Get-Content -LiteralPath (Join-Path $dir "heartbeat_latest.json") -Raw | ConvertFrom-Json
  $current = Get-Content -LiteralPath (Join-Path $dir "current_task_latest.json") -Raw | ConvertFrom-Json
  $status = Get-Content -LiteralPath (Join-Path $dir "status_latest.json") -Raw | ConvertFrom-Json
  foreach ($item in @($ownership, $checkpoint, $heartbeat, $current, $status)) {
    if ($item.slot_id -ne $slotId) { throw "CROSS_SLOT_FILE: $slotId" }
  }
  if (-not $ownership.wrong_slot_write_forbidden) { throw "WRONG_SLOT_GUARD_MISSING: $slotId" }
  if (-not $checkpoint.zip_timestamp_ignored) { throw "ZIP_TIMESTAMP_GUARD_MISSING: $slotId" }
  if ($checkpoint.first_unverified_step -ne "READ_REMOTE_BUSINESS_STATE") { throw "REMOTE_FIRST_CHECKPOINT_MISSING: $slotId" }
}
$gates = Get-Content -LiteralPath (Join-Path $slotRoot "gates_status_latest.json") -Raw | ConvertFrom-Json
if ($gates.shared_publish_gate.state -ne "unclaimed") { throw "INITIAL_SHARED_GATE_NOT_CLEAN" }
if ($manifest.local_runner_concurrency -ne 1 -or -not $manifest.single_runner_only) { throw "SINGLE_RUNNER_CONTRACT_FAILED" }

[ordered]@{
  status = "PASS"
  workstream_id = $manifest.workstream_id
  slot_count = 5
  slot_ids = $actual
  unique_slot_ids = $true
  wrong_slot_guard = $true
  remote_first_checkpoint = $true
  zip_timestamp_ignored = $true
  shared_publish_gate = $true
  remote_parallel_slots = 5
  local_runner_concurrency = 1
  new_runner = $false
  parallel_runner = $false
  final_ready = $false
} | ConvertTo-Json -Depth 10
