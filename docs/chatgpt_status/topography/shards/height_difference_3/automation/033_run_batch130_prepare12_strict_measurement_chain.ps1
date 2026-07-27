param(
  [Parameter(Mandatory=$false)][string]$RepoRoot = $env:AAYS_REPO_ROOT,
  [Parameter(Mandatory=$false)][string]$PythonExe = "python",
  [Parameter(Mandatory=$false)][string]$PowerShellExe = $env:AAYS_POWERSHELL_EXE
)
$ErrorActionPreference = "Stop"
if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
  $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..\..\..\..")).Path
}
if ([string]::IsNullOrWhiteSpace($PowerShellExe)) { $PowerShellExe = "powershell" }

$Prepare12 = Join-Path $RepoRoot "docs\chatgpt_status\topography\shards\height_difference_3\automation\032_run_batch129_range_extract_and_prepare12.ps1"
$ProjGate = Join-Path $RepoRoot "docs\chatgpt_status\topography\shards\height_difference_3\automation\034_verify_candidate_manifest_proj_ostn15_gate.py"
$TerrainDownload = Join-Path $RepoRoot "docs\chatgpt_status\topography\shards\height_difference_3\automation\021_download_os_terrain50_via_api.py"
$Pipeline = Join-Path $RepoRoot "docs\chatgpt_status\topography\shards\height_difference_3\automation\015_execute_auto_source_and_measurement_pipeline.py"
$QueryOut = Join-Path $RepoRoot "docs\chatgpt_status\topography\shards\height_difference_3\runner_outputs\025_batch129_prepare12_queries"
$Starter = Join-Path $QueryOut "starter_three_query_manifest.json"
$Out = Join-Path $RepoRoot "docs\chatgpt_status\topography\shards\height_difference_3\runner_outputs\027_batch130_prepare12_strict_chain"
$TerrainOut = Join-Path $Out "terrain50_download"
$MeasureOut = Join-Path $Out "measurement"
$ProjOut = Join-Path $Out "00_proj_ostn15_gate.json"
$TerrainProv = Join-Path $TerrainOut "terrain50_official_api_provenance.json"

foreach ($P in @($Prepare12,$ProjGate,$TerrainDownload,$Pipeline)) {
  if (-not (Test-Path -LiteralPath $P -PathType Leaf)) { throw "Missing required script: $P" }
}
New-Item -ItemType Directory -Force -Path $Out,$TerrainOut,$MeasureOut | Out-Null

& $PowerShellExe -NoProfile -ExecutionPolicy Bypass -File $Prepare12 -RepoRoot $RepoRoot -PythonExe $PythonExe -PowerShellExe $PowerShellExe
if ($LASTEXITCODE -ne 0) { throw "Prepare12 chain failed with exit code $LASTEXITCODE" }
if (-not (Test-Path -LiteralPath $Starter -PathType Leaf)) { throw "Missing prepare12 starter manifest" }

& $PythonExe $ProjGate `
  --candidate-manifest $Starter `
  --output $ProjOut `
  --enable-network `
  --expected-row-start 61540 `
  --expected-row-end 61551 `
  --maximum-display-delta-m 20.0
if ($LASTEXITCODE -ne 0) { throw "Candidate-aware PROJ OSTN15 strict gate failed with exit code $LASTEXITCODE" }
if (-not (Test-Path -LiteralPath $ProjOut -PathType Leaf)) { throw "Missing candidate-aware PROJ gate output" }
$Pj = Get-Content -Raw -LiteralPath $ProjOut | ConvertFrom-Json
$Expected = 61540..61551
$ProjRows = @($Pj.candidate_rows | ForEach-Object { [int]$_ })
if (-not [bool]$Pj.passed) { throw "Candidate-aware PROJ gate did not pass" }
if (($ProjRows -join ',') -ne ($Expected -join ',')) { throw "PROJ gate candidate rows are not exactly 61540..61551" }
if (-not [bool]$Pj.best_available) { throw "PROJ best operation unavailable" }
if ([bool]$Pj.best_transformer.contains_ballpark) { throw "PROJ ballpark transformation is forbidden" }
if (-not [bool]$Pj.best_transformer.uses_ostn15_grid) { throw "PROJ best transformation does not use OSTN15 grid" }
if (-not [bool]$Pj.all_display_deltas_within_sanity_limit) { throw "PROJ display coordinate delta exceeds sanity limit" }

& $PythonExe $TerrainDownload --output-dir $TerrainOut --timeout 120 --max-cache-age-hours 24
if ($LASTEXITCODE -ne 0) { throw "Terrain50 official acquisition failed with exit code $LASTEXITCODE" }
$TerrainArchive = Join-Path $TerrainOut "OS_Terrain50_July_2026_GB_ASCII_Grid.zip"
if (-not (Test-Path -LiteralPath $TerrainArchive -PathType Leaf)) { throw "Missing current Terrain50 archive" }
if (-not (Test-Path -LiteralPath $TerrainProv -PathType Leaf)) { throw "Missing Terrain50 official provenance manifest" }
$TP = Get-Content -Raw -LiteralPath $TerrainProv | ConvertFrom-Json
if (-not [bool]$TP.official_catalog_verified) { throw "Terrain50 official catalog verification is missing" }
if ([string]$TP.product_id -ne "Terrain50" -or [string]$TP.area -ne "GB" -or [string]$TP.format -ne "ASCII Grid and GML (Grid)") { throw "Terrain50 provenance identity mismatch" }
if ([string]::IsNullOrWhiteSpace([string]$TP.catalog_sha256) -or ([string]$TP.catalog_sha256).Length -ne 64) { throw "Terrain50 catalog SHA256 is missing" }
if ([string]::IsNullOrWhiteSpace([string]$TP.archive_sha256) -or ([string]$TP.archive_sha256).Length -ne 64) { throw "Terrain50 archive SHA256 is missing" }
if ([int64]$TP.archive_size_bytes -ne (Get-Item -LiteralPath $TerrainArchive).Length) { throw "Terrain50 archive size does not match provenance" }
$TerrainHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $TerrainArchive).Hash.ToLowerInvariant()
if ($TerrainHash -ne ([string]$TP.archive_sha256).ToLowerInvariant()) { throw "Terrain50 archive SHA256 does not match provenance" }
if ([bool]$TP.cache_reused -and -not [bool]$TP.cache_provenance_verified) { throw "Terrain50 cache reuse lacks provenance verification" }

& $PythonExe $Pipeline `
  --starter-manifest $Starter `
  --terrain50-source $TerrainArchive `
  --output-dir $MeasureOut `
  --timeout 120 `
  --maximum-crosscheck-difference-m 8.0 `
  --require-exact-official-id
if ($LASTEXITCODE -ne 0) { throw "Official 12-candidate measurement pipeline failed with exit code $LASTEXITCODE" }

$HmlrSource = Join-Path $MeasureOut "sources\hmlr_source_manifest.json"
$EaSource = Join-Path $MeasureOut "sources\ea_dtm_source_manifest.json"
$TerrainSource = Join-Path $MeasureOut "sources\terrain50_source_manifest.json"
foreach ($P in @($HmlrSource,$EaSource,$TerrainSource)) {
  if (-not (Test-Path -LiteralPath $P -PathType Leaf)) { throw "Missing official source manifest: $P" }
}
$HS = Get-Content -Raw -LiteralPath $HmlrSource | ConvertFrom-Json
$ES = Get-Content -Raw -LiteralPath $EaSource | ConvertFrom-Json
$TS = Get-Content -Raw -LiteralPath $TerrainSource | ConvertFrom-Json
if ([string]$HS.status -ne "READY" -or [int]$HS.schema_version -lt 3) { throw "HMLR source manifest is not strict-ready" }
if ([string]$HS.official_entry_host -ne "use-land-property-data.service.gov.uk") { throw "HMLR official entry host mismatch" }
if ([string]$HS.authority_match_policy -ne "EXACT_NORMALIZED_AUTHORITY_CONTEXT_OR_HREF_ONLY") { throw "HMLR exact authority source policy missing" }
if ([bool]$HS.nearest_or_fuzzy_authority_match_used) { throw "HMLR fuzzy authority source match is forbidden" }
if (@($HS.records).Count -lt 1) { throw "HMLR source manifest contains no authority record" }
foreach ($R in @($HS.records)) {
  if ([string]$R.authority_match_method -ne "EXACT_NORMALIZED_AUTHORITY_CONTEXT_OR_HREF") { throw "HMLR authority record is not exact" }
  if (-not [bool]$R.trusted_redirect) { throw "HMLR authority record lacks trusted redirect proof" }
  if (@($R.vectors).Count -lt 1) { throw "HMLR authority record contains no vector" }
  foreach ($Vec in @($R.vectors)) {
    if ([string]::IsNullOrWhiteSpace([string]$Vec.sha256) -or ([string]$Vec.sha256).Length -ne 64) { throw "HMLR vector SHA256 is missing" }
  }
}
if ([string]$ES.status -ne "READY" -or [int]$ES.schema_version -lt 2) { throw "EA DTM source manifest is not strict-ready" }
if ([string]$ES.official_host -ne "environment.data.gov.uk" -or -not [bool]$ES.official_host_only) { throw "EA DTM official host gate missing" }
if ([bool]$ES.axis_labels_inferred) { throw "EA WCS axis labels must be discovered, not inferred" }
if (@($ES.axis_labels).Count -ne 2) { throw "EA WCS axis labels are missing" }
if ([string]$TS.status -ne "READY") { throw "Terrain50 extracted source manifest is not ready" }
if ([bool]$TS.nearest_or_neighbour_tile_substitution_used) { throw "Terrain50 nearest/neighbour tile substitution is forbidden" }
if ([int]$TS.candidate_count -ne 12) { throw "Terrain50 source manifest candidate count is not 12" }

$Measurement = Join-Path $MeasureOut "official_measurements.json"
$Verified = Join-Path $MeasureOut "verified_examples.json"
if (-not (Test-Path -LiteralPath $Measurement -PathType Leaf)) { throw "Missing official measurement manifest" }
if (-not (Test-Path -LiteralPath $Verified -PathType Leaf)) { throw "Missing verified examples manifest" }
$M = Get-Content -Raw -LiteralPath $Measurement | ConvertFrom-Json
$V = Get-Content -Raw -LiteralPath $Verified | ConvertFrom-Json
$MeasuredRows = @($M.measured_rows | ForEach-Object { [int]$_.row_no })
$PublishedRows = @($V.rows | ForEach-Object { [int]$_.row_no })
if (($MeasuredRows -join ',') -ne ($Expected -join ',')) { throw "Measured row set is not exactly 61540..61551" }
if (($PublishedRows -join ',') -ne ($Expected -join ',')) { throw "Published row set is not exactly 61540..61551" }
if ([int]$V.published_example_count -ne 12) { throw "Expected exactly 12 verified examples" }
$ResultRows = @($M.results)
if ($ResultRows.Count -ne 12) { throw "Expected exactly 12 measurement result rows" }
foreach ($R in $ResultRows) {
  $HmlrMethod = [string]$R.hmlr_match_method
  if (-not $HmlrMethod.StartsWith("EXACT_OFFICIAL_ID")) { throw "Strict12 requires exact HMLR official-ID boundary match for row $($R.row_no); got $HmlrMethod" }
  if ([bool]$R.nearest_point_fill_used) { throw "Nearest-point fill is forbidden for row $($R.row_no)" }
}
foreach ($R in $M.measured_rows) {
  if ($R.height_difference_method -ne "EA_DTM_1M_POLYGON_P95_MINUS_P05") { throw "Unexpected height-difference method" }
  if (@("HIGH","MEDIUM_HIGH") -notcontains [string]$R.confidence) { throw "Unapproved confidence" }
  if ([int]$R.ea_valid_cell_count -lt 4) { throw "Insufficient EA cell count" }
  if ([double]$R.cross_source_absolute_difference_m -gt 8.0) { throw "Cross-source difference exceeds 8m" }
  $BoundaryMethod = [string]$R.boundary_match_method
  if (-not $BoundaryMethod.StartsWith("EXACT_OFFICIAL_ID")) { throw "Measured row lacks exact HMLR official-ID boundary match: $($R.row_no) / $BoundaryMethod" }
}

$Result = @{
  schema_version = 6
  slot_id = "height_difference_3"
  same_task_resume_only = $true
  prepared_and_measured_rows = $Expected
  verified_count = 12
  python_executable = $PythonExe
  powershell_executable = $PowerShellExe
  executable_identity_propagated = $true
  method = "EA_DTM_1M_POLYGON_P95_MINUS_P05"
  minimum_ea_cells = 4
  maximum_crosscheck_difference_m = 8.0
  allowed_confidence = @("HIGH","MEDIUM_HIGH")
  proj_ostn15_gate = $true
  proj_gate_candidate_rows = $ProjRows
  proj_gate_candidate_aware = $true
  proj_maximum_display_delta_m = 20.0
  exact_hmlr_official_id_gate = $true
  exact_hmlr_gate_runs_before_elevation_sampling = $true
  hmlr_exact_authority_source_gate = $true
  ea_official_host_and_axis_metadata_gate = $true
  terrain50_official_catalog_archive_hash_gate = $true
  nearest_fill_forbidden = $true
  numeric_publish_gate_passed = $true
  remote_readback_required = $true
  final_ready = $false
  fake_data = $false
}
$ResultPath = Join-Path $Out "batch130_strict12_acceptance.json"
$Result | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 -LiteralPath $ResultPath
Write-Output ($Result | ConvertTo-Json -Compress -Depth 8)
