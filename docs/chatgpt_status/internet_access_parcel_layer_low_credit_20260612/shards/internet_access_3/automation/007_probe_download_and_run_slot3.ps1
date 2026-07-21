param(
  [Parameter(Mandatory=$true)][string]$RepoRoot,
  [string]$WorkRoot = "",
  [int]$DownloadRetries = 4
)

$ErrorActionPreference = 'Stop'
$SlotId = 'internet_access_3'
$ZipUrl = 'https://www.ofcom.org.uk/siteassets/resources/documents/research-and-data/multi-sector/infrastructure-research/connected-nations-spring-2026/202601_fixed_broadband_coverage_and_full_fibre_take-up-r1.zip?v=422620'
if (-not $WorkRoot) { $WorkRoot = Join-Path $RepoRoot 'outputs/internet_access_3_verified_run' }
$AutomationRoot = Join-Path $RepoRoot 'docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/automation'
$CanonicalSource = Join-Path $RepoRoot 'england_map_web/data/program_layer_matrix/security.geojson'
$LegacySource = Join-Path $RepoRoot 'england_map_web/data/program_layer_matrix/internet.geojson'
$StageRoot = Join-Path $WorkRoot 'stage'
$ExtractRoot = Join-Path $WorkRoot 'ofcom_extract'
$SliceRoot = Join-Path $WorkRoot 'slot_inputs'
$OutputRoot = Join-Path $WorkRoot 'candidate_outputs'
$ZipPath = Join-Path $StageRoot '202601_fixed_broadband_coverage_and_full_fibre_take-up-r1.zip'
$PartialZip = "$ZipPath.part"
$DiagnosticsPath = Join-Path $WorkRoot 'internet_access_3_network_and_execution_diagnostics_latest.json'

New-Item -ItemType Directory -Force -Path $WorkRoot,$StageRoot,$SliceRoot,$OutputRoot | Out-Null
$diagnostics = [ordered]@{
  schema_version = 3
  slot_id = $SlotId
  started_at = (Get-Date).ToUniversalTime().ToString('o')
  official_zip_url = $ZipUrl
  canonical_source = $CanonicalSource
  legacy_source = $LegacySource
  dns_state = 'NOT_CHECKED'
  download_state = 'NOT_STARTED'
  download_attempts = @()
  zip_sha256 = $null
  zip_bytes = 0
  r2_file_count = 0
  r1_file_count = 0
  canonical_slice_rows = $null
  candidate_manifest = $null
  actual_business_data_rows_written = 0
  scores_written = 0
  db_write = $false
  migration = $false
  production_deploy = $false
  final_ready = $false
}

function Save-Diagnostics([string]$state, [string]$message) {
  $diagnostics['state'] = $state
  $diagnostics['message'] = $message
  $diagnostics['updated_at'] = (Get-Date).ToUniversalTime().ToString('o')
  $diagnostics | ConvertTo-Json -Depth 12 | Set-Content -Path $DiagnosticsPath -Encoding UTF8
}

try {
  foreach ($required in @($CanonicalSource,$LegacySource)) {
    if (-not (Test-Path -LiteralPath $required)) { throw "Required source missing: $required" }
  }

  try {
    $dns = Resolve-DnsName -Name 'www.ofcom.org.uk' -Type A -ErrorAction Stop
    $diagnostics.dns_state = 'PASS'
    $diagnostics.dns_addresses = @($dns | Where-Object {$_.IPAddress} | ForEach-Object {$_.IPAddress})
  } catch {
    $diagnostics.dns_state = 'FAIL'
    $diagnostics.dns_error = $_.Exception.Message
    Save-Diagnostics 'BLOCKED_DNS' 'Official source host could not be resolved. No data was written.'
    exit 2
  }

  if (Test-Path -LiteralPath $PartialZip) { Remove-Item -Force -LiteralPath $PartialZip }
  $downloaded = $false
  for ($attempt = 1; $attempt -le $DownloadRetries; $attempt++) {
    $entry = [ordered]@{attempt=$attempt; started_at=(Get-Date).ToUniversalTime().ToString('o'); state='STARTED'}
    try {
      Invoke-WebRequest -Uri $ZipUrl -OutFile $PartialZip -UseBasicParsing -TimeoutSec 600 -MaximumRedirection 8 -Headers @{'User-Agent'='AAYS-internet_access_3-verifier/3'}
      $length = (Get-Item -LiteralPath $PartialZip).Length
      if ($length -lt 30000000) { throw "Downloaded ZIP is unexpectedly small: $length bytes" }
      $signature = [System.IO.File]::ReadAllBytes($PartialZip)[0..1]
      if ($signature[0] -ne 0x50 -or $signature[1] -ne 0x4B) { throw 'Downloaded file does not have a ZIP signature' }
      Move-Item -Force -LiteralPath $PartialZip -Destination $ZipPath
      $entry.state = 'PASS'; $entry.bytes = $length
      $diagnostics.download_attempts += $entry
      $downloaded = $true
      break
    } catch {
      $entry.state = 'FAIL'; $entry.error = $_.Exception.Message
      $diagnostics.download_attempts += $entry
      if (Test-Path -LiteralPath $PartialZip) { Remove-Item -Force -LiteralPath $PartialZip }
      if ($attempt -lt $DownloadRetries) { Start-Sleep -Seconds ([Math]::Min(30, [Math]::Pow(2,$attempt))) }
    }
  }
  if (-not $downloaded) { throw "Official ZIP download failed after $DownloadRetries attempts" }

  $diagnostics.download_state = 'PASS'
  $diagnostics.zip_bytes = (Get-Item -LiteralPath $ZipPath).Length
  $diagnostics.zip_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $ZipPath).Hash.ToLowerInvariant()

  if (Test-Path -LiteralPath $ExtractRoot) { Remove-Item -Recurse -Force -LiteralPath $ExtractRoot }
  Expand-Archive -LiteralPath $ZipPath -DestinationPath $ExtractRoot -Force
  $r1 = @(Get-ChildItem -Path $ExtractRoot -Recurse -File -Filter '202601_fixed_postcode_coverage_r1_*.csv')
  $r2 = @(Get-ChildItem -Path $ExtractRoot -Recurse -File -Filter '202601_fixed_postcode_coverage_r2_*.csv')
  $diagnostics.r1_file_count = $r1.Count
  $diagnostics.r2_file_count = $r2.Count
  if ($r1.Count -ne 0) { throw "Superseded all-premises r1 postcode files found: $($r1.Count)" }
  if ($r2.Count -ne 121) { throw "Expected 121 corrected r2 postcode files, found $($r2.Count)" }

  & python (Join-Path $AutomationRoot '005_stream_extract_slot3_inputs.py') --canonical $CanonicalSource --legacy-internet $LegacySource --output-dir $SliceRoot
  if ($LASTEXITCODE -ne 0) { throw "Streaming slot extraction failed with exit code $LASTEXITCODE" }

  $sliceManifestPath = Join-Path $SliceRoot 'internet_access_3_stream_slice_manifest_latest.json'
  $sliceManifest = Get-Content -Raw -LiteralPath $sliceManifestPath | ConvertFrom-Json
  $diagnostics.canonical_slice_rows = $sliceManifest.canonical.rows
  if ($diagnostics.canonical_slice_rows -ne 30761) { throw "Canonical slice row count mismatch: $($diagnostics.canonical_slice_rows)" }

  & python (Join-Path $AutomationRoot '002_extract_slot3_ofcom_2026_candidates.py') `
    --canonical (Join-Path $SliceRoot 'internet_access_3_canonical_slice_latest.geojson') `
    --legacy-internet-geojson (Join-Path $SliceRoot 'internet_access_3_legacy_slice_latest.geojson') `
    --ofcom-postcode-dir $ExtractRoot `
    --output-dir $OutputRoot
  if ($LASTEXITCODE -ne 0) { throw "Ofcom join failed with exit code $LASTEXITCODE" }

  $candidateManifestPath = Join-Path $OutputRoot 'internet_access_3_candidate_manifest_latest.json'
  $candidateManifest = Get-Content -Raw -LiteralPath $candidateManifestPath | ConvertFrom-Json
  $diagnostics.candidate_manifest = $candidateManifestPath
  $diagnostics.current_r2_postcode_proxy_rows = $candidateManifest.current_r2_postcode_proxy_rows
  $diagnostics.identity_conflict_rows = $candidateManifest.identity_conflict_rows
  $diagnostics.no_data_rows = $candidateManifest.no_data_rows
  Save-Diagnostics 'COMPLETE_REVIEW_OUTPUT_READY' 'Official bytes, hashes, bounded canonical slice and review-only join completed. No migration or business write occurred.'
  exit 0
} catch {
  $diagnostics.error = $_.Exception.Message
  Save-Diagnostics 'BLOCKED_EXECUTION' 'Execution stopped at a verified gate. No migration or business write occurred.'
  exit 2
}
