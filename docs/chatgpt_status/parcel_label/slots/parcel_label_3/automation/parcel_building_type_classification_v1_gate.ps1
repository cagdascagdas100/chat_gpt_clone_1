param()

$ErrorActionPreference = "Stop"

function Write-JsonFile {
    param(
        [Parameter(Mandatory=$true)][string]$Path,
        [Parameter(Mandatory=$true)]$Value
    )
    $parent = Split-Path -Parent $Path
    if ($parent) {
        New-Item -ItemType Directory -Force -Path $parent | Out-Null
    }
    $tmp = "$Path.tmp.$PID"
    $Value | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $tmp -Encoding UTF8
    Move-Item -LiteralPath $tmp -Destination $Path -Force
}

$repoRoot = $env:AAYS_REPO_ROOT
if (-not $repoRoot) {
    $repoRoot = (& git rev-parse --show-toplevel).Trim()
}
$slotId = $env:AAYS_SLOT_ID
if (-not $slotId) {
    throw "AAYS_SLOT_ID is required"
}
if ($slotId -notmatch '^parcel_label_[123]$') {
    throw "UNSUPPORTED_SLOT_ID: $slotId"
}

$partitionBySlot = @{
    parcel_label_1 = @{ start = 1; end = 30761; count = 30761 }
    parcel_label_2 = @{ start = 30762; end = 61522; count = 30761 }
    parcel_label_3 = @{ start = 61523; end = 92283; count = 30761 }
}
$partition = $partitionBySlot[$slotId]
$now = [DateTimeOffset]::UtcNow.ToString("o")

$candidateSources = @(
    "docs/chatgpt_status/parcel_label/slots/$slotId/runner_outputs",
    "england_map_web/data/distance_property_types",
    "england_map_web/data/aays_21_slots/$slotId",
    "england_map_web/data/program_layer_matrix",
    "england_map_web/data/parcels"
)

$sourceInventory = @()
foreach ($relative in $candidateSources) {
    $absolute = Join-Path $repoRoot $relative
    $exists = Test-Path -LiteralPath $absolute
    $fileCount = 0
    if ($exists) {
        $fileCount = @(Get-ChildItem -LiteralPath $absolute -File -Recurse -ErrorAction SilentlyContinue | Select-Object -First 5001).Count
    }
    $sourceInventory += [ordered]@{
        path = $relative
        exists = $exists
        file_count_capped_at_5001 = $fileCount
    }
}

$usableEvidence = @($sourceInventory | Where-Object { $_.exists -and $_.file_count_capped_at_5001 -gt 0 })
$state = "BLOCKED_SOURCE_DISCOVERY_REQUIRED"
$reason = "No authoritative parcel/building-type classification source manifest is available yet. This gate did not infer or fabricate labels."
if ($usableEvidence.Count -gt 0) {
    $state = "READY_FOR_PARCEL_BUILDING_TYPE_PIPELINE_IMPLEMENTATION"
    $reason = "Existing local candidate evidence roots were found; next step is implementing the source-specific classifier with evidence manifests."
}

$payload = [ordered]@{
    schema_version = 1
    slot_id = $slotId
    phase_id = "parcel_building_type_classification_v1"
    state = $state
    final_ready = $false
    fake_data = $false
    parcel_partition = $partition
    source_discovery_policy = "LOCAL_FILES_THEN_FREE_PUBLIC_NO_AUTH"
    measurement_level = "parcel_only_after_direct_evidence"
    output_semantics = "NO_FAKE_LABELS"
    source_inventory = $sourceInventory
    usable_evidence_root_count = $usableEvidence.Count
    reason = $reason
    next_required_actions = @(
        "Implement OSM/Overture/EPC/VOA/UPRN evidence adapters only where source licence and local cache are available.",
        "Write labels only with URL/accessed_at/SHA-256/source_scope/source_granularity/field evidence.",
        "Keep raw downloads in runtime cache; publish only derived rows and small evidence manifests.",
        "Leave parcels unknown when evidence is absent."
    )
    updated_at = $now
}

$runnerOut = Join-Path $repoRoot "docs/chatgpt_status/aays1/shards/$slotId/runner_outputs/${slotId}_building_type_classification_latest.json"
$reconcileOut = Join-Path $repoRoot "docs/chatgpt_status/aays1/shards/$slotId/runner_outputs/${slotId}_building_type_classification_reconciliation_latest.json"

Write-JsonFile -Path $runnerOut -Value $payload
Write-JsonFile -Path $reconcileOut -Value $payload

Write-Host "$slotId $state"
if ($state -eq "READY_FOR_PARCEL_BUILDING_TYPE_PIPELINE_IMPLEMENTATION") {
    exit 0
}
exit 2
