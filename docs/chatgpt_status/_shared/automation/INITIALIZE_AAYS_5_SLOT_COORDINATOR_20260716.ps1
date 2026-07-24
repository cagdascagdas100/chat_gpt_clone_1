[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)]
  [string]$RepoRoot,
  [string]$RuntimeStatusPath,
  [switch]$CreateMissing
)

$ErrorActionPreference = "Stop"
$WorkstreamId = "AAYS_5_SLOT_SAFE_PARALLEL_V1"
$Branch = "codex/aays-single-runner-v5-20260706"
$SlotRoot = Join-Path $RepoRoot "docs\chatgpt_status\_shared\slots"
$Utf8 = New-Object System.Text.UTF8Encoding($false)

$Slots = @(
  [ordered]@{ slot_id = "ready_to_sell"; display_name = "ReadyToSell"; page_key = "aays1"; business_status_root = "docs/chatgpt_status/aays1"; required_filename_markers = @("ready_to_sell", "geometry_review") },
  [ordered]@{ slot_id = "gas_emissions"; display_name = "Gas Emissions"; page_key = "gas_emissions"; business_status_root = "docs/chatgpt_status/gas_emissions"; required_filename_markers = @("gas_emissions", "gas_emission") },
  [ordered]@{ slot_id = "height_difference"; display_name = "Height Difference"; page_key = "topography"; business_status_root = "docs/chatgpt_status/topography"; required_filename_markers = @("topography", "height_difference", "height_differance") },
  [ordered]@{ slot_id = "security_public_safety"; display_name = "Security"; page_key = "aays1"; business_status_root = "docs/chatgpt_status/aays1"; required_filename_markers = @("security", "public_safety") },
  [ordered]@{ slot_id = "parcel_label"; display_name = "Parcel Label"; page_key = "aays1"; business_status_root = "docs/chatgpt_status/aays1"; required_filename_markers = @("parcel_label", "distance_property_types") }
)

function Write-JsonAtomic {
  param([string]$Path, [object]$Value)
  $directory = Split-Path -Parent $Path
  if (-not (Test-Path -LiteralPath $directory)) {
    New-Item -ItemType Directory -Force -Path $directory | Out-Null
  }
  $temporary = "$Path.tmp.$([guid]::NewGuid().ToString('N'))"
  [System.IO.File]::WriteAllText($temporary, ($Value | ConvertTo-Json -Depth 20) + [Environment]::NewLine, $Utf8)
  Move-Item -LiteralPath $temporary -Destination $Path -Force
}

function Write-JsonIfMissing {
  param([string]$Path, [object]$Value)
  if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
    Write-JsonAtomic -Path $Path -Value $Value
  }
}

function Read-RequiredJson {
  param([string]$Path)
  if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
    throw "REQUIRED_SLOT_FILE_MISSING: $Path"
  }
  try {
    return Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json
  } catch {
    throw "INVALID_SLOT_JSON: $Path :: $($_.Exception.Message)"
  }
}

$ManifestSlots = @()
foreach ($slot in $Slots) {
  $id = $slot.slot_id
  $stateRoot = "docs/chatgpt_status/_shared/slots/$id"
  $ManifestSlots += [ordered]@{
    slot_id = $id
    display_name = $slot.display_name
    page_key = $slot.page_key
    business_status_root = $slot.business_status_root
    state_paths = [ordered]@{
      checkpoint = "$stateRoot/checkpoint_latest.json"
      heartbeat = "$stateRoot/heartbeat_latest.json"
      current_task = "$stateRoot/current_task_latest.json"
      status = "$stateRoot/status_latest.json"
      ownership = "$stateRoot/ownership_latest.json"
    }
    write_scope = [ordered]@{
      slot_state_root = $stateRoot
      business_status_root = $slot.business_status_root
      required_filename_markers = $slot.required_filename_markers
      shared_publish_gate_required = $true
      other_slot_roots_forbidden = $true
    }
  }
}

$Manifest = [ordered]@{
  schema_version = 1
  workstream_id = $WorkstreamId
  branch = $Branch
  authoritative_source = "github_remote_branch_head"
  zip_state_is_historical = $true
  coordination_model = "parallel_chatgpt_slots_serialized_single_local_runner"
  remote_slots_can_progress_in_parallel = $true
  local_runner_concurrency = 1
  single_runner_only = $true
  duplicate_runner_forbidden = $true
  slot_count = 5
  lease_timeout_seconds = 900
  claim_rule = "Only the matching ZIP SLOT_ID may claim the slot. A live foreign lease blocks writes. A stale lease may be replaced only after remote HEAD readback."
  shared_publish_rule = "Shared application/index files require the single shared_publish_gate; business slot state remains isolated."
  slots = $ManifestSlots
  safety = [ordered]@{ final_ready = $false; product_final_ready = $false; fake_data = $false; db_write = $false; migration = $false; production_deploy = $false }
}

if ($CreateMissing) {
  Write-JsonIfMissing -Path (Join-Path $SlotRoot "manifest_latest.json") -Value $Manifest
  $SlotSummaries = @()
  foreach ($slot in $Slots) {
    $id = $slot.slot_id
    $directory = Join-Path $SlotRoot $id
    $SlotSummaries += [ordered]@{ slot_id = $id; state = "ready_for_claim"; owner_page_session_id = $null; current_task_id = $null; first_unverified_step = "READ_REMOTE_BUSINESS_STATE" }
    Write-JsonIfMissing -Path (Join-Path $directory "checkpoint_latest.json") -Value ([ordered]@{
      schema_version = 1; workstream_id = $WorkstreamId; slot_id = $id; sequence = 0
      authoritative_source = "github_remote_branch_head"; zip_timestamp_ignored = $true
      last_verified_remote_commit = $null; last_completed_step = $null
      first_unverified_step = "READ_REMOTE_BUSINESS_STATE"; completed_task_ids = @(); terminal_task_replay_forbidden = $true
      updated_at = $null; final_ready = $false
    })
    Write-JsonIfMissing -Path (Join-Path $directory "heartbeat_latest.json") -Value ([ordered]@{
      schema_version = 1; workstream_id = $WorkstreamId; slot_id = $id; state = "unclaimed"
      owner_page_session_id = $null; heartbeat_at = $null; stale = $true; stale_after_seconds = 900
      current_task_id = $null; source = "remote_slot_owner_only"; final_ready = $false
    })
    Write-JsonIfMissing -Path (Join-Path $directory "current_task_latest.json") -Value ([ordered]@{
      schema_version = 1; workstream_id = $WorkstreamId; slot_id = $id; task_id = $null
      state = "idle"; owner_page_session_id = $null; claimed_at = $null; allowed_paths = @()
      terminal = $false; replay_forbidden = $true; final_ready = $false
    })
    Write-JsonIfMissing -Path (Join-Path $directory "ownership_latest.json") -Value ([ordered]@{
      schema_version = 1; workstream_id = $WorkstreamId; slot_id = $id; lease_version = 0
      state = "unclaimed"; owner_page_session_id = $null; owner_zip_slot_id = $null
      lease_token_hash = $null; claimed_at = $null; heartbeat_at = $null; lease_expires_at = $null
      takeover_rule = "Only when lease is absent or stale, after reading current GitHub HEAD."
      wrong_slot_write_forbidden = $true; final_ready = $false
    })
    Write-JsonIfMissing -Path (Join-Path $directory "status_latest.json") -Value ([ordered]@{
      schema_version = 1; workstream_id = $WorkstreamId; slot_id = $id; state = "ready_for_claim"
      page_key = $slot.page_key; business_status_root = $slot.business_status_root
      owner_page_session_id = $null; current_task_id = $null; blocker = $null
      first_unverified_step = "READ_REMOTE_BUSINESS_STATE"; shared_publish_gate_required = $true
      authoritative_source = "github_remote_branch_head"; zip_timestamp_ignored = $true; final_ready = $false
    })
  }
  Write-JsonIfMissing -Path (Join-Path $SlotRoot "slots_status_latest.json") -Value ([ordered]@{
    schema_version = 1; workstream_id = $WorkstreamId; state = "ready"; slot_count = 5
    remote_parallel_slots = 5; local_runner_concurrency = 1; slots = $SlotSummaries
    updated_at = $null; final_ready = $false
  })
  Write-JsonIfMissing -Path (Join-Path $SlotRoot "gates_status_latest.json") -Value ([ordered]@{
    schema_version = 1; workstream_id = $WorkstreamId
    shared_publish_gate = [ordered]@{
      state = "unclaimed"; owner_slot_id = $null; owner_page_session_id = $null
      lease_version = 0; claimed_at = $null; heartbeat_at = $null; lease_expires_at = $null
      protected_paths = @("england_map_web/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html", "england_map_web/geometry_review_3of4_columns_1264.html", "docs/chatgpt_status/_shared/status", "docs/chatgpt_status/_shared/reports")
      rule = "Exactly one live slot owner may publish shared paths. Slot-local evidence may progress in parallel."
    }
    final_ready = $false
  })
}

$ParsedManifest = Read-RequiredJson -Path (Join-Path $SlotRoot "manifest_latest.json")
if ($ParsedManifest.workstream_id -ne $WorkstreamId -or [int]$ParsedManifest.slot_count -ne 5) {
  throw "INVALID_SLOT_MANIFEST_IDENTITY"
}
$Seen = @{}
$Validation = @()
foreach ($slot in $Slots) {
  $id = $slot.slot_id
  if ($Seen.ContainsKey($id)) { throw "DUPLICATE_SLOT_ID: $id" }
  $Seen[$id] = $true
  $directory = Join-Path $SlotRoot $id
  foreach ($name in @("checkpoint_latest.json", "heartbeat_latest.json", "current_task_latest.json", "status_latest.json", "ownership_latest.json")) {
    $value = Read-RequiredJson -Path (Join-Path $directory $name)
    if ($value.slot_id -ne $id -or $value.workstream_id -ne $WorkstreamId) {
      throw "CROSS_SLOT_IDENTITY_MISMATCH: $id/$name"
    }
  }
  $Validation += [ordered]@{ slot_id = $id; valid = $true }
}
$null = Read-RequiredJson -Path (Join-Path $SlotRoot "slots_status_latest.json")
$null = Read-RequiredJson -Path (Join-Path $SlotRoot "gates_status_latest.json")

$Result = [ordered]@{
  status = "READY"
  workstream_id = $WorkstreamId
  slot_count = 5
  slots = $Validation
  remote_parallel_slots = 5
  local_runner_concurrency = 1
  wrong_slot_write_guard = $true
  live_lease_guard = $true
  stale_takeover_requires_remote_head = $true
  shared_publish_gate = $true
  new_runner = $false
  parallel_runner = $false
  final_ready = $false
  product_final_ready = $false
  fake_data = $false
  db_write = $false
  migration = $false
  production_deploy = $false
  validated_at = (Get-Date).ToUniversalTime().ToString("o")
}
if ($RuntimeStatusPath) {
  Write-JsonAtomic -Path $RuntimeStatusPath -Value $Result
}
$Result | ConvertTo-Json -Depth 10
