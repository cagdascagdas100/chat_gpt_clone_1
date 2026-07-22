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

function New-VerifiedHmlrMainScript {
  param([string]$SourcePath)
  $source = [System.IO.File]::ReadAllText($SourcePath, [System.Text.Encoding]::UTF8).Replace("`r`n", "`n")
  $oldBlock = @'
        page_bytes, page_headers = fetch_bytes(
            HMLR_DOWNLOAD_PAGE, timeout=180, retries=3, max_bytes=20_000_000
        )
        gml_url = args.hmlr_gml_url or discover_hmlr_gml_url(page_bytes)
        gml_bytes, gml_headers = fetch_bytes(
            gml_url, timeout=300, retries=3, max_bytes=MAX_GML_BYTES
        )
'@
  $newBlock = @'
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
  $matchCount = [regex]::Matches($source, [regex]::Escape($oldBlock)).Count
  if ($matchCount -ne 1) { throw "MAIN_HMLR_BLOCK_MATCH_COUNT_INVALID: $matchCount" }
  $patched = $source.Replace($oldBlock, $newBlock)
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
Write-Output 'TASK_VERSION=1.5-hmlr-zip-verified-handoff'
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
  $pageHash = (Get-FileHash -LiteralPath $tempPage -Algorithm SHA256).Hash.ToLowerInvariant()
  $gmlHash = (Get-FileHash -LiteralPath $tempGml -Algorithm SHA256).Hash.ToLowerInvariant()
  if ($pageHash -ne ([string]$hmlrDocument.artifacts.download_page.sha256).ToLowerInvariant()) { throw 'HMLR_PAGE_HASH_HANDOFF_MISMATCH' }
  if ($gmlHash -ne ([string]$hmlrDocument.artifacts.hmlr_gml.sha256).ToLowerInvariant()) { throw 'HMLR_GML_HASH_HANDOFF_MISMATCH' }
  if ((Get-Item -LiteralPath $tempPage).Length -ne [int64]$hmlrDocument.artifacts.download_page.bytes) { throw 'HMLR_PAGE_SIZE_HANDOFF_MISMATCH' }
  if ((Get-Item -LiteralPath $tempGml).Length -ne [int64]$hmlrDocument.artifacts.hmlr_gml.bytes) { throw 'HMLR_GML_SIZE_HANDOFF_MISMATCH' }
  Write-Output "HMLR_ZIP_SHA256=$($hmlrDocument.artifacts.hmlr_zip.sha256)"
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
  Remove-Item -LiteralPath $tempMetadataMap -Force -ErrorAction SilentlyContinue
  Remove-Item -LiteralPath $tempPage -Force -ErrorAction SilentlyContinue
  Remove-Item -LiteralPath $tempGml -Force -ErrorAction SilentlyContinue
}
