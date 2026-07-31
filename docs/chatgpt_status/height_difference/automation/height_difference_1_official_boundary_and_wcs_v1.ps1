[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$repoRoot = if ($env:AAYS_REPO_ROOT) {
  [System.IO.Path]::GetFullPath($env:AAYS_REPO_ROOT)
} else {
  [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..\..'))
}

function Resolve-RepoScript {
  param([string]$RepoPath, [string]$TempName)
  $local = Join-Path $repoRoot ($RepoPath -replace '/', '\')
  if (Test-Path -LiteralPath $local -PathType Leaf) { return $local }
  $git = Get-Command git -ErrorAction SilentlyContinue
  if (-not $git) { throw "GIT_EXECUTABLE_NOT_FOUND_FOR_SCRIPT_FALLBACK: $RepoPath" }
  $tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) 'aays_height_difference_1'
  New-Item -ItemType Directory -Path $tempRoot -Force | Out-Null
  $temp = Join-Path $tempRoot $TempName
  foreach ($ref in @('origin/agent/height-difference-1-main-clean-r4-20260722','origin/main','main')) {
    $scriptText = & $git.Source -C $repoRoot show "$ref`:$RepoPath" 2>$null
    if ($LASTEXITCODE -eq 0 -and $null -ne $scriptText) {
      [System.IO.File]::WriteAllText($temp, (($scriptText -join [Environment]::NewLine) + [Environment]::NewLine), [System.Text.UTF8Encoding]::new($false))
      if ((Test-Path -LiteralPath $temp -PathType Leaf) -and ((Get-Item -LiteralPath $temp).Length -gt 0)) {
        return $temp
      }
    }
  }
  throw "REPOSITORY_SCRIPT_MISSING: $RepoPath"
}

function Replace-ExactlyOnce {
  param([string]$Text, [string]$Old, [string]$New, [string]$Label)
  $matchCount = [regex]::Matches($Text, [regex]::Escape($Old)).Count
  if ($matchCount -ne 1) { throw "$Label`_MATCH_COUNT_INVALID: $matchCount" }
  return $Text.Replace($Old, $New)
}

function New-VerifiedHmlrMainScript {
  param([string]$SourcePath)
  $patched = [System.IO.File]::ReadAllText($SourcePath, [System.Text.Encoding]::UTF8).Replace("`r`n", "`n")

  $oldHmlr = @'
        page_bytes, page_headers = fetch_bytes(
            HMLR_DOWNLOAD_PAGE, timeout=180, retries=3, max_bytes=20_000_000
        )
        gml_url = args.hmlr_gml_url or discover_hmlr_gml_url(page_bytes)
        gml_bytes, gml_headers = fetch_bytes(
            gml_url, timeout=300, retries=3, max_bytes=MAX_GML_BYTES
        )
'@
  $newHmlr = @'
        verified_page_file = os.environ.get("HMLR_VERIFIED_PAGE_FILE")
        verified_gml_file = os.environ.get("HMLR_VERIFIED_GML_FILE")
        if args.hmlr_gml_url and verified_page_file and verified_gml_file:
            page_path = Path(verified_page_file).resolve()
            gml_path = Path(verified_gml_file).resolve()
            page_bytes = page_path.read_bytes()
            gml_bytes = gml_path.read_bytes()
            if not page_bytes or not gml_bytes:
                raise EvidenceError("VERIFIED_HMLR_HANDOFF_EMPTY")
            if len(page_bytes) > 20_000_000 or len(gml_bytes) > MAX_GML_BYTES:
                raise EvidenceError("VERIFIED_HMLR_HANDOFF_SIZE_LIMIT")
            page_headers = {"content-type": "text/html"}
            gml_headers = {"content-type": "application/gml+xml"}
            gml_url = args.hmlr_gml_url
        else:
            page_bytes, page_headers = fetch_bytes(
                HMLR_DOWNLOAD_PAGE, timeout=180, retries=3, max_bytes=20_000_000
            )
            gml_url = args.hmlr_gml_url or discover_hmlr_gml_url(page_bytes)
            gml_bytes, gml_headers = fetch_bytes(
                gml_url, timeout=300, retries=3, max_bytes=MAX_GML_BYTES
            )
'@
  $patched = Replace-ExactlyOnce -Text $patched -Old $oldHmlr -New $newHmlr -Label 'MAIN_HMLR_BLOCK'

  $oldMetadataValidator = @'
def validate_survey_metadata_entry(parcel_id: str, entry: Any) -> dict[str, Any]:
    if not isinstance(entry, dict):
        raise EvidenceError(f"SURVEY_METADATA_MISSING:{parcel_id}")
    source_url = str(entry.get("source_url", ""))
    parsed = urlparse(source_url)
    if parsed.scheme != "https" or parsed.netloc != "environment.data.gov.uk":
        raise EvidenceError(f"SURVEY_METADATA_SOURCE_NOT_OFFICIAL_EA:{parcel_id}")
    survey_date = entry.get("survey_date")
    survey_year = entry.get("survey_year")
    if survey_date:
        try:
            parsed_date = dt.date.fromisoformat(str(survey_date))
        except ValueError as exc:
            raise EvidenceError(f"SURVEY_DATE_NOT_ISO:{parcel_id}") from exc
        if not (2000 <= parsed_date.year <= dt.date.today().year):
            raise EvidenceError(f"SURVEY_DATE_OUT_OF_RANGE:{parcel_id}")
    elif survey_year is not None:
        year = int(survey_year)
        if not (2000 <= year <= dt.date.today().year):
            raise EvidenceError(f"SURVEY_YEAR_OUT_OF_RANGE:{parcel_id}")
    else:
        raise EvidenceError(f"SURVEY_DATE_OR_YEAR_REQUIRED:{parcel_id}")
    if str(entry.get("resolution_state", "")).upper() not in {"RESOLVED", "OFFICIAL_METADATA_RESOLVED"}:
        raise EvidenceError(f"SURVEY_METADATA_NOT_RESOLVED:{parcel_id}")
    return dict(entry)
'@
  $newMetadataValidator = @'
def validate_survey_metadata_entry(parcel_id: str, entry: Any) -> dict[str, Any]:
    if not isinstance(entry, dict):
        raise EvidenceError(f"SURVEY_METADATA_MISSING:{parcel_id}")
    source_url = str(entry.get("source_url", ""))
    parsed = urlparse(source_url)
    if parsed.scheme != "https" or parsed.netloc != "environment.data.gov.uk":
        raise EvidenceError(f"SURVEY_METADATA_SOURCE_NOT_OFFICIAL_EA:{parcel_id}")
    expected_crs = "http://www.opengis.net/def/crs/EPSG/0/27700"
    if entry.get("source_collection") != "LIDAR_Composite_1m_DTM_2022_extents":
        raise EvidenceError(f"SURVEY_METADATA_COLLECTION_MISMATCH:{parcel_id}")
    if entry.get("request_bbox_crs") != expected_crs or entry.get("response_geometry_crs") != expected_crs:
        raise EvidenceError(f"SURVEY_METADATA_CRS_MISMATCH:{parcel_id}")
    for field in ("ogc_response_sha256", "feature_properties_sha256"):
        digest = str(entry.get(field, "")).lower()
        if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
            raise EvidenceError(f"SURVEY_METADATA_HASH_INVALID:{parcel_id}:{field}")
    for field in ("filename", "tilename", "polygon_id"):
        if not str(entry.get(field, "")).strip():
            raise EvidenceError(f"SURVEY_METADATA_FIELD_MISSING:{parcel_id}:{field}")
    resolution = float(entry.get("resolution_m"))
    if not math.isfinite(resolution) or not (0.25 <= resolution <= 2.0):
        raise EvidenceError(f"SURVEY_METADATA_RESOLUTION_INVALID:{parcel_id}:{resolution}")
    try:
        parsed_date = dt.date.fromisoformat(str(entry.get("survey_date")))
        parsed_end = dt.date.fromisoformat(str(entry.get("survey_end_date")))
        year = int(entry.get("survey_year"))
    except Exception as exc:
        raise EvidenceError(f"SURVEY_METADATA_DATE_YEAR_INVALID:{parcel_id}") from exc
    if parsed_end < parsed_date:
        raise EvidenceError(f"SURVEY_METADATA_DATE_ORDER_INVALID:{parcel_id}")
    if not (2000 <= parsed_date.year <= dt.date.today().year and 2000 <= parsed_end.year <= dt.date.today().year):
        raise EvidenceError(f"SURVEY_METADATA_DATE_OUT_OF_RANGE:{parcel_id}")
    if year not in {parsed_date.year, parsed_end.year}:
        raise EvidenceError(f"SURVEY_METADATA_YEAR_DATE_MISMATCH:{parcel_id}")
    if str(entry.get("resolution_state", "")).upper() != "OFFICIAL_METADATA_RESOLVED":
        raise EvidenceError(f"SURVEY_METADATA_NOT_RESOLVED:{parcel_id}")
    return dict(entry)
'@
  $patched = Replace-ExactlyOnce -Text $patched -Old $oldMetadataValidator -New $newMetadataValidator -Label 'SURVEY_METADATA_VALIDATOR'

  $oldProbeGate = @'
                qa_pair = [
                    probe_by_parcel_product[(parcel_id, "DTM_1M")],
                    probe_by_parcel_product[(parcel_id, "DSM_LZ_1M")],
                ]
                item["probe_qa_states"] = [row["state"] for row in qa_pair]
                if any(row["state"] != "TIFF_BYTES_AND_CRS_VERIFIED" for row in qa_pair):
                    raise EvidenceError("PARCEL_DTM_DSM_10M_QA_PAIR_NOT_VERIFIED")
'@
  $newProbeGate = @'
                dtm_probe = probe_by_parcel_product[(parcel_id, "DTM_1M")]
                dsm_probe = probe_by_parcel_product[(parcel_id, "DSM_LZ_1M")]
                item["probe_qa_states"] = {
                    "DTM_1M": dtm_probe["state"],
                    "DSM_LZ_1M": dsm_probe["state"],
                }
                if dtm_probe["state"] != "TIFF_BYTES_AND_CRS_VERIFIED":
                    raise EvidenceError("PARCEL_DTM_10M_QA_NOT_VERIFIED")
                if dsm_probe["state"] != "TIFF_BYTES_AND_CRS_VERIFIED":
                    item["errors"].append("PARCEL_DSM_10M_QA_UNAVAILABLE")
'@
  $patched = Replace-ExactlyOnce -Text $patched -Old $oldProbeGate -New $newProbeGate -Label 'DTM_DSM_PROBE_GATE'

  $oldFullRaster = @'
                full_receipts: dict[str, Any] = {}
                for product, endpoint, coverage in (
                    ("DTM_1M", DTM_ENDPOINT, DTM_COVERAGE),
                    ("DSM_LZ_1M", DSM_ENDPOINT, DSM_COVERAGE),
                ):
                    url = wcs_url(endpoint, coverage, bbox)
                    data, headers = fetch_bytes(url, timeout=300, retries=3, max_bytes=MAX_TIFF_BYTES)
                    validate_tiff_bytes(data, headers.get("content-type"))
                    tif = workdir / f"{parcel_id}_{product}.tif"
                    tif.write_bytes(data)
                    measurement = raster_measurement(tif, polygon, rasterio, np, mask, mapping)
                    full_receipts[product] = {
                        "url": url,
                        "sha256": sha256_bytes(data),
                        "bytes": len(data),
                        "content_type": headers.get("content-type"),
                        "measurement": measurement,
                    }
                item["full_polygon_rasters"] = full_receipts
                dtm = full_receipts["DTM_1M"]["measurement"]
                dsm = full_receipts["DSM_LZ_1M"]["measurement"]
                item["measurement_state"] = "OFFICIAL_BYTES_AND_GEOMETRY_MEASURED"
                item["candidate_height_difference_m"] = dtm["height_difference_m"]
                item["dsm_qa_height_range_m"] = dsm["height_difference_m"]
'@
  $newFullRaster = @'
                full_receipts: dict[str, Any] = {}
                dtm_url = wcs_url(DTM_ENDPOINT, DTM_COVERAGE, bbox)
                dtm_data, dtm_headers = fetch_bytes(dtm_url, timeout=300, retries=3, max_bytes=MAX_TIFF_BYTES)
                validate_tiff_bytes(dtm_data, dtm_headers.get("content-type"))
                dtm_tif = workdir / f"{parcel_id}_DTM_1M.tif"
                dtm_tif.write_bytes(dtm_data)
                dtm_measurement = raster_measurement(dtm_tif, polygon, rasterio, np, mask, mapping)
                full_receipts["DTM_1M"] = {
                    "state": "REQUIRED_TERRAIN_VERIFIED",
                    "url": dtm_url,
                    "sha256": sha256_bytes(dtm_data),
                    "bytes": len(dtm_data),
                    "content_type": dtm_headers.get("content-type"),
                    "measurement": dtm_measurement,
                }
                try:
                    dsm_url = wcs_url(DSM_ENDPOINT, DSM_COVERAGE, bbox)
                    dsm_data, dsm_headers = fetch_bytes(dsm_url, timeout=300, retries=3, max_bytes=MAX_TIFF_BYTES)
                    validate_tiff_bytes(dsm_data, dsm_headers.get("content-type"))
                    dsm_tif = workdir / f"{parcel_id}_DSM_LZ_1M.tif"
                    dsm_tif.write_bytes(dsm_data)
                    dsm_measurement = raster_measurement(dsm_tif, polygon, rasterio, np, mask, mapping)
                    full_receipts["DSM_LZ_1M"] = {
                        "state": "OPTIONAL_SURFACE_QA_VERIFIED",
                        "url": dsm_url,
                        "sha256": sha256_bytes(dsm_data),
                        "bytes": len(dsm_data),
                        "content_type": dsm_headers.get("content-type"),
                        "measurement": dsm_measurement,
                    }
                except Exception as dsm_exc:
                    full_receipts["DSM_LZ_1M"] = {
                        "state": "OPTIONAL_SURFACE_QA_UNAVAILABLE",
                        "error": str(dsm_exc),
                    }
                    item["errors"].append(f"DSM_FULL_POLYGON_QA_UNAVAILABLE:{dsm_exc}")
                item["full_polygon_rasters"] = full_receipts
                dtm = full_receipts["DTM_1M"]["measurement"]
                dsm_measurement = full_receipts["DSM_LZ_1M"].get("measurement")
                item["measurement_state"] = "OFFICIAL_DTM_BYTES_AND_GEOMETRY_MEASURED"
                item["candidate_height_difference_m"] = dtm["height_difference_m"]
                item["dsm_qa_height_range_m"] = (
                    dsm_measurement.get("height_difference_m") if dsm_measurement else None
                )
'@
  $patched = Replace-ExactlyOnce -Text $patched -Old $oldFullRaster -New $newFullRaster -Label 'FULL_POLYGON_DTM_DSM_BLOCK'

  $oldCandidateHashes = @'
                    "hmlr_gml_sha256": result["artifacts"]["hmlr_gml"]["sha256"],
                    "dtm_sha256": full_receipts["DTM_1M"]["sha256"],
                    "dsm_sha256": full_receipts["DSM_LZ_1M"]["sha256"],
'@
  $newCandidateHashes = @'
                    "hmlr_gml_sha256": result["artifacts"]["hmlr_gml"]["sha256"],
                    "hmlr_zip_sha256": os.environ.get("HMLR_VERIFIED_ZIP_SHA256"),
                    "hmlr_zip_final_host": os.environ.get("HMLR_VERIFIED_ZIP_FINAL_HOST"),
                    "dtm_sha256": full_receipts["DTM_1M"]["sha256"],
                    "dsm_sha256": full_receipts.get("DSM_LZ_1M", {}).get("sha256"),
'@
  $patched = Replace-ExactlyOnce -Text $patched -Old $oldCandidateHashes -New $newCandidateHashes -Label 'CANDIDATE_PROVENANCE_HASHES'

  $oldMetadataStart = @'
                item["candidate"] = candidate
                try:
                    metadata = validate_survey_metadata_entry(parcel_id, survey_metadata.get(parcel_id))
'@
  $newMetadataStart = @'
                item["candidate"] = candidate
                zip_digest = str(candidate.get("hmlr_zip_sha256") or "").lower()
                if len(zip_digest) != 64 or any(char not in "0123456789abcdef" for char in zip_digest):
                    raise EvidenceError("HMLR_ZIP_SHA256_REQUIRED_FOR_BUSINESS_ROW")
                if candidate.get("hmlr_zip_final_host") not in {
                    "use-land-property-data.service.gov.uk",
                    "datapub-prd-s3-bucket.s3.amazonaws.com",
                }:
                    raise EvidenceError("HMLR_ZIP_FINAL_HOST_REQUIRED_FOR_BUSINESS_ROW")
                try:
                    metadata = validate_survey_metadata_entry(parcel_id, survey_metadata.get(parcel_id))
'@
  $patched = Replace-ExactlyOnce -Text $patched -Old $oldMetadataStart -New $newMetadataStart -Label 'BUSINESS_ROW_PROVENANCE_GATE'

  $tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) 'aays_height_difference_1'
  New-Item -ItemType Directory -Path $tempRoot -Force | Out-Null
  $patchedPath = Join-Path $tempRoot 'height_difference_1_official_boundary_and_wcs_verified_handoff.py'
  [System.IO.File]::WriteAllText($patchedPath, $patched, [System.Text.UTF8Encoding]::new($false))
  if (-not (Test-Path -LiteralPath $patchedPath -PathType Leaf)) { throw 'PATCHED_MAIN_SCRIPT_MISSING' }
  return $patchedPath
}

$mainRepoPath = 'docs/chatgpt_status/height_difference/automation/height_difference_1_official_boundary_and_wcs_v1.py'
$metadataRepoPath = 'docs/chatgpt_status/height_difference/automation/height_difference_1_ea_survey_metadata_v1.py'
$hmlrRepoPath = 'docs/chatgpt_status/height_difference/automation/height_difference_1_hmlr_zip_resolver_v1.py'
$mainScript = Resolve-RepoScript -RepoPath $mainRepoPath -TempName 'height_difference_1_official_boundary_and_wcs_v1.py'
$metadataScript = Resolve-RepoScript -RepoPath $metadataRepoPath -TempName 'height_difference_1_ea_survey_metadata_v1.py'
$hmlrScript = Resolve-RepoScript -RepoPath $hmlrRepoPath -TempName 'height_difference_1_hmlr_zip_resolver_v1.py'
$patchedMainScript = New-VerifiedHmlrMainScript -SourcePath $mainScript

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) { $python = Get-Command py -ErrorAction SilentlyContinue }
if (-not $python) { throw 'PYTHON_EXECUTABLE_NOT_FOUND' }

function Invoke-Python {
  param([string[]]$Arguments)
  $lines = if ($python.Name -eq 'py.exe' -or $python.Name -eq 'py') {
    & $python.Source -3 @Arguments 2>&1
  } else {
    & $python.Source @Arguments 2>&1
  }
  $code = $LASTEXITCODE
  if ($null -eq $code) { $code = 1 }
  foreach ($line in @($lines)) { [Console]::Out.WriteLine([string]$line) }
  return [int]$code
}

$runnerOutput = Join-Path $repoRoot 'docs\chatgpt_status\height_difference\shards\height_difference_1\runner_outputs\official_boundary_and_wcs_latest.json'
$metadataOutput = Join-Path $repoRoot 'docs\chatgpt_status\height_difference\shards\height_difference_1\runner_outputs\official_survey_metadata_latest.json'
$hmlrReceipt = Join-Path $repoRoot 'docs\chatgpt_status\height_difference\shards\height_difference_1\runner_outputs\official_hmlr_zip_gml_latest.json'
$websiteOutput = Join-Path $repoRoot 'england_map_web\data\aays_18_slots\height_difference_1\verified_results_latest.json'
$tempMetadataMap = Join-Path ([System.IO.Path]::GetTempPath()) 'height_difference_1_official_survey_metadata_map.json'
$tempPage = Join-Path ([System.IO.Path]::GetTempPath()) 'height_difference_1_hmlr_download_page.html'
$tempGml = Join-Path ([System.IO.Path]::GetTempPath()) 'height_difference_1_barking_dagenham_current.gml'

Write-Output 'SLOT_ID=height_difference_1'
Write-Output 'TASK_VERSION=1.7-dtm-required-dsm-optional-provenance-strict'
Write-Output "REPO_ROOT=$repoRoot"
Write-Output "MAIN_SCRIPT=$mainScript"
Write-Output "PATCHED_MAIN_SCRIPT=$patchedMainScript"
Write-Output "METADATA_SCRIPT=$metadataScript"
Write-Output "HMLR_ZIP_SCRIPT=$hmlrScript"
Write-Output 'SINGLE_SHARED_RUNNER_ONLY=true'
Write-Output 'NEW_RUNNER_ALLOWED=false'
Write-Output 'RUNNER_EXECUTION_CLAIMED=true'
Write-Output 'DB_WRITE=false'
Write-Output 'MIGRATION=false'
Write-Output 'PRODUCTION_DEPLOY=false'

try {
  $hmlrSelfTest = Invoke-Python -Arguments @($hmlrScript, '--self-test')
  Write-Output "HMLR_ZIP_SELF_TEST_EXIT_CODE=$hmlrSelfTest"
  if ($hmlrSelfTest -ne 0) { Write-Output 'FINAL_READY=false'; exit $hmlrSelfTest }

  $metadataSelfTest = Invoke-Python -Arguments @($metadataScript, '--self-test')
  Write-Output "METADATA_SELF_TEST_EXIT_CODE=$metadataSelfTest"
  if ($metadataSelfTest -ne 0) { Write-Output 'FINAL_READY=false'; exit $metadataSelfTest }

  $mainSelfTest = Invoke-Python -Arguments @($patchedMainScript, '--self-test')
  Write-Output "MAIN_SELF_TEST_EXIT_CODE=$mainSelfTest"
  if ($mainSelfTest -ne 0) { Write-Output 'FINAL_READY=false'; exit $mainSelfTest }

  $hmlrExit = Invoke-Python -Arguments @(
    $hmlrScript,
    '--page-output', $tempPage,
    '--gml-output', $tempGml,
    '--receipt-output', $hmlrReceipt
  )
  Write-Output "HMLR_ZIP_PYTHON_EXIT_CODE=$hmlrExit"
  if ($hmlrExit -ne 0) { Write-Output 'FINAL_READY=false'; exit $hmlrExit }
  foreach ($requiredFile in @($tempPage, $tempGml, $hmlrReceipt)) {
    if (-not (Test-Path -LiteralPath $requiredFile -PathType Leaf)) { throw "HMLR_HANDOFF_FILE_MISSING: $requiredFile" }
  }
  $hmlrDocument = Get-Content -LiteralPath $hmlrReceipt -Raw -Encoding UTF8 | ConvertFrom-Json
  if ($hmlrDocument.slot_id -ne 'height_difference_1' -or $hmlrDocument.state -ne 'COMPLETED_ZIP_AND_GML_VERIFIED') {
    throw 'HMLR_ZIP_RECEIPT_INVALID'
  }
  $allowedZipHosts = @('use-land-property-data.service.gov.uk','datapub-prd-s3-bucket.s3.amazonaws.com')
  $zipFinalHost = [string]$hmlrDocument.artifacts.hmlr_zip.final_host
  if ($hmlrDocument.artifacts.hmlr_zip.final_host_allowlisted -ne $true -or $allowedZipHosts -notcontains $zipFinalHost) {
    throw "HMLR_ZIP_FINAL_HOST_HANDOFF_INVALID: $zipFinalHost"
  }
  $pageFinalHost = [string]$hmlrDocument.artifacts.download_page.final_host
  if ($pageFinalHost -ne 'use-land-property-data.service.gov.uk') { throw "HMLR_PAGE_FINAL_HOST_HANDOFF_INVALID: $pageFinalHost" }
  $pageHash = (Get-FileHash -LiteralPath $tempPage -Algorithm SHA256).Hash.ToLowerInvariant()
  $gmlHash = (Get-FileHash -LiteralPath $tempGml -Algorithm SHA256).Hash.ToLowerInvariant()
  $zipHash = ([string]$hmlrDocument.artifacts.hmlr_zip.sha256).ToLowerInvariant()
  if ($zipHash -notmatch '^[0-9a-f]{64}$') { throw 'HMLR_ZIP_HASH_HANDOFF_INVALID' }
  if ($pageHash -ne ([string]$hmlrDocument.artifacts.download_page.sha256).ToLowerInvariant()) { throw 'HMLR_PAGE_HASH_HANDOFF_MISMATCH' }
  if ($gmlHash -ne ([string]$hmlrDocument.artifacts.hmlr_gml.sha256).ToLowerInvariant()) { throw 'HMLR_GML_HASH_HANDOFF_MISMATCH' }
  if ((Get-Item -LiteralPath $tempPage).Length -ne [int64]$hmlrDocument.artifacts.download_page.bytes) { throw 'HMLR_PAGE_SIZE_HANDOFF_MISMATCH' }
  if ((Get-Item -LiteralPath $tempGml).Length -ne [int64]$hmlrDocument.artifacts.hmlr_gml.bytes) { throw 'HMLR_GML_SIZE_HANDOFF_MISMATCH' }
  Write-Output "HMLR_ZIP_FINAL_HOST=$zipFinalHost"
  Write-Output "HMLR_ZIP_SHA256=$zipHash"
  Write-Output "HMLR_GML_SHA256=$gmlHash"

  $metadataExit = Invoke-Python -Arguments @(
    $metadataScript,
    '--repo-root', $repoRoot,
    '--output', $metadataOutput,
    '--max-workers', '4'
  )
  Write-Output "METADATA_PYTHON_EXIT_CODE=$metadataExit"
  if ($metadataExit -eq 2) { Write-Output 'FINAL_READY=false'; exit $metadataExit }
  if (-not (Test-Path -LiteralPath $metadataOutput -PathType Leaf)) { throw 'OFFICIAL_SURVEY_METADATA_OUTPUT_MISSING' }
  $metadataDocument = Get-Content -LiteralPath $metadataOutput -Raw -Encoding UTF8 | ConvertFrom-Json
  if ($metadataDocument.slot_id -ne 'height_difference_1' -or $null -eq $metadataDocument.metadata) { throw 'OFFICIAL_SURVEY_METADATA_OUTPUT_INVALID' }
  $metadataJson = $metadataDocument.metadata | ConvertTo-Json -Depth 20
  [System.IO.File]::WriteAllText($tempMetadataMap, ($metadataJson + [Environment]::NewLine), [System.Text.UTF8Encoding]::new($false))
  $resolvedRows = @($metadataDocument.metadata.PSObject.Properties).Count
  Write-Output "SURVEY_METADATA_RESOLVED_ROWS=$resolvedRows"

  $env:HMLR_VERIFIED_PAGE_FILE = $tempPage
  $env:HMLR_VERIFIED_GML_FILE = $tempGml
  $env:HMLR_VERIFIED_ZIP_SHA256 = $zipHash
  $env:HMLR_VERIFIED_ZIP_FINAL_HOST = $zipFinalHost
  $gmlUri = ([System.Uri]::new($tempGml)).AbsoluteUri
  $mainExit = Invoke-Python -Arguments @(
    $patchedMainScript,
    '--repo-root', $repoRoot,
    '--runner-output', $runnerOutput,
    '--website-output', $websiteOutput,
    '--survey-metadata-json', $tempMetadataMap,
    '--hmlr-gml-url', $gmlUri,
    '--max-workers', '4'
  )
  Write-Output "MAIN_PYTHON_EXIT_CODE=$mainExit"
  Write-Output 'FINAL_READY=false'
  exit $mainExit
} finally {
  Remove-Item Env:HMLR_VERIFIED_PAGE_FILE -ErrorAction SilentlyContinue
  Remove-Item Env:HMLR_VERIFIED_GML_FILE -ErrorAction SilentlyContinue
  Remove-Item Env:HMLR_VERIFIED_ZIP_SHA256 -ErrorAction SilentlyContinue
  Remove-Item Env:HMLR_VERIFIED_ZIP_FINAL_HOST -ErrorAction SilentlyContinue
  Remove-Item -LiteralPath $tempMetadataMap -Force -ErrorAction SilentlyContinue
  Remove-Item -LiteralPath $tempPage -Force -ErrorAction SilentlyContinue
  Remove-Item -LiteralPath $tempGml -Force -ErrorAction SilentlyContinue
}
