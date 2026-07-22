[CmdletBinding()]
param(
  [string]$EpochPolicy = $env:AAYS_HD3_EPOCH_POLICY
)

$ErrorActionPreference = 'Stop'
$root = [System.IO.Path]::GetFullPath([string]$env:AAYS_REPO_ROOT)
if ([string]::IsNullOrWhiteSpace($root)) { throw 'AAYS_REPO_ROOT_REQUIRED' }

$sourceBranch = 'codex/aays-single-runner-v5-20260706'
$expectedBlob = 'bb48164e7a0af78df875f30421a6a3068c43edb8'
$epochEvidenceRel = 'docs/chatgpt_status/height_difference/runner_inputs/height_difference_3_epoch_policy_latest.json'
$chainReportRel = 'docs/chatgpt_status/height_difference/runner_outputs/height_difference_3_chain_orchestration_latest.json'
$websiteReportRel = 'england_map_web/data/height_difference/height_difference_3_chain_orchestration_latest.json'
$canonicalRel = 'docs/chatgpt_status/height_difference/runner_outputs/height_difference_3_canonical_points_latest.json'
$discoveryRel = 'docs/chatgpt_status/height_difference/runner_outputs/height_difference_3_official_discovery_latest.json'
$manifestRel = 'docs/chatgpt_status/height_difference/runner_outputs/height_difference_3_official_input_manifest_latest.json'
$samplingRel = 'docs/chatgpt_status/height_difference/runner_outputs/height_difference_3_boundary_raster_sampling_latest.json'

function Resolve-RepoPath([string]$Rel) {
  return (Join-Path $root ($Rel.Replace('/','\')))
}
function Read-Json([string]$Rel) {
  $path = Resolve-RepoPath $Rel
  if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw ('INPUT_NOT_FOUND:' + $Rel) }
  return (Get-Content -LiteralPath $path -Raw | ConvertFrom-Json)
}
function Write-JsonAtomic([string]$Rel, [object]$Payload) {
  $path = Resolve-RepoPath $Rel
  $dir = Split-Path -Parent $path
  New-Item -ItemType Directory -Force -Path $dir | Out-Null
  $tmp = $path + '.tmp'
  [System.IO.File]::WriteAllText($tmp, ($Payload | ConvertTo-Json -Depth 80), [System.Text.UTF8Encoding]::new($false))
  Move-Item -LiteralPath $tmp -Destination $path -Force
}
function Invoke-Step([string]$Name, [string]$ScriptRel, [string[]]$Arguments = @()) {
  $script = Resolve-RepoPath $ScriptRel
  if (-not (Test-Path -LiteralPath $script -PathType Leaf)) { throw ('STEP_SCRIPT_NOT_FOUND:' + $Name) }
  $output = & powershell -NoProfile -ExecutionPolicy Bypass -File $script @Arguments 2>&1
  $code = $LASTEXITCODE
  return [pscustomobject]@{ name=$Name; script=$ScriptRel; exit_code=$code; output=(($output | Out-String).Trim()); passed=($code -eq 0) }
}
function Assert-Canonical([object]$Doc) {
  if (-not $Doc.acceptance.passed) { throw 'CANONICAL_ACCEPTANCE_NOT_PASSED' }
  if ($Doc.source.git_blob_sha -ne $expectedBlob) { throw 'CANONICAL_BLOB_SHA_MISMATCH' }
  if ($Doc.canonical_point_row_count -ne 3) { throw 'CANONICAL_POINT_ROW_COUNT_NOT_3' }
  $ids = @($Doc.canonical_point_rows | ForEach-Object { [string]$_.parcel_id })
  if (($ids -join ',') -ne 'parcel_61523,parcel_61524,parcel_61525') { throw 'CANONICAL_POINT_ORDER_INVALID' }
}
function Accepted-EpochEvidence([string]$RequestedPolicy) {
  $accepted = @('ETRS89_EQUIVALENCE_PROVEN','WGS84_TO_ETRS89_TRANSFORM_PROVEN')
  if (-not ($accepted -contains $RequestedPolicy)) { return $null }
  $path = Resolve-RepoPath $epochEvidenceRel
  if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { return $null }
  $doc = Get-Content -LiteralPath $path -Raw | ConvertFrom-Json
  if ($doc.slot_id -ne 'height_difference_3') { return $null }
  if (-not [bool]$doc.accepted) { return $null }
  if ($doc.policy -ne $RequestedPolicy) { return $null }
  if ($doc.canonical_blob_sha -ne $expectedBlob) { return $null }
  if ($null -eq $doc.evidence_sources -or @($doc.evidence_sources).Count -lt 1) { return $null }
  return $doc
}

$startedAt = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
$steps = @()
$state = 'STARTED'
$blockers = @()

try {
  Push-Location $root
  try {
    $fetch = & git fetch --no-tags origin "$sourceBranch`:refs/heads/$sourceBranch" 2>&1
    if ($LASTEXITCODE -ne 0) { throw ('HISTORICAL_BRANCH_FETCH_FAILED:' + (($fetch | Out-String).Trim())) }
    $resolved = (& git rev-parse "$sourceBranch`:england_map_web/data/parcel_security_scores_rechecked_0_120m_spatial.geojson").Trim()
    if ($LASTEXITCODE -ne 0 -or $resolved -ne $expectedBlob) { throw ('HISTORICAL_BRANCH_BLOB_MISMATCH:' + $resolved) }
  } finally { Pop-Location }

  $extract = Invoke-Step 'canonical_point_extract' 'docs/chatgpt_status/height_difference/automation/height_difference_3_extract_canonical_points_v1_1.ps1'
  $steps += $extract
  if (-not $extract.passed) { throw 'CANONICAL_POINT_EXTRACT_FAILED' }
  $canonical = Read-Json $canonicalRel
  Assert-Canonical $canonical

  $epochEvidence = Accepted-EpochEvidence $EpochPolicy
  if ($null -eq $epochEvidence) {
    $state = 'BLOCKED_EPOCH_PROVENANCE'
    $blockers += 'CANONICAL_POINT_CRS_EPOCH_PROVENANCE_NOT_CONFIRMED'
  } else {
    $discovery = Invoke-Step 'official_discovery' 'docs/chatgpt_status/height_difference/automation/height_difference_3_post_point_official_discovery_v1.ps1' @('-EpochPolicy',$EpochPolicy)
    $steps += $discovery
    if (-not $discovery.passed -or -not (Test-Path -LiteralPath (Resolve-RepoPath $discoveryRel))) { throw 'OFFICIAL_DISCOVERY_FAILED' }

    $manifest = Invoke-Step 'official_input_manifest' 'docs/chatgpt_status/height_difference/automation/height_difference_3_official_input_manifest_v1.ps1'
    $steps += $manifest
    if (-not $manifest.passed -or -not (Test-Path -LiteralPath (Resolve-RepoPath $manifestRel))) { throw 'OFFICIAL_INPUT_MANIFEST_FAILED' }

    $sampling = Invoke-Step 'boundary_raster_sampling' 'docs/chatgpt_status/height_difference/automation/height_difference_3_boundary_raster_sampling_v1.ps1'
    $steps += $sampling
    if (-not $sampling.passed -or -not (Test-Path -LiteralPath (Resolve-RepoPath $samplingRel))) { throw 'BOUNDARY_RASTER_SAMPLING_FAILED' }
    $state = 'CHAIN_EXECUTION_PASS_NONFINAL'
  }
} catch {
  $state = 'CHAIN_EXECUTION_BLOCKED'
  $blockers += $_.Exception.Message
}

$report = [ordered]@{
  schema_version = 1
  slot_id = 'height_difference_3'
  task_id = 'height-difference-3-single-pass-chain-v1-20260722'
  started_at = $startedAt
  completed_at = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
  state = $state
  source_branch = $sourceBranch
  expected_blob_sha = $expectedBlob
  epoch_policy_requested = $EpochPolicy
  epoch_evidence_path = $epochEvidenceRel
  steps = @($steps)
  blockers = @($blockers | Select-Object -Unique)
  canonical_point_output_exists = (Test-Path -LiteralPath (Resolve-RepoPath $canonicalRel))
  official_discovery_output_exists = (Test-Path -LiteralPath (Resolve-RepoPath $discoveryRel))
  official_input_manifest_output_exists = (Test-Path -LiteralPath (Resolve-RepoPath $manifestRel))
  boundary_raster_sampling_output_exists = (Test-Path -LiteralPath (Resolve-RepoPath $samplingRel))
  output_semantics = 'SINGLE_SHARED_RUNNER_SEQUENTIAL_CHAIN_FAIL_CLOSED_NONFINAL'
  actual_business_data_rows_written = 0
  fake_data = $false
  db_write = $false
  migration = $false
  production_deploy = $false
  final_ready = $false
}
Write-JsonAtomic $chainReportRel $report
Write-JsonAtomic $websiteReportRel $report
Write-Host ('HEIGHT_DIFFERENCE_3_CHAIN_STATE=' + $state)
Write-Host ('HEIGHT_DIFFERENCE_3_CHAIN_STEPS=' + @($steps).Count)
Write-Host 'FINAL_READY=false'

if ($state -eq 'CHAIN_EXECUTION_BLOCKED') { exit 2 }
exit 0
