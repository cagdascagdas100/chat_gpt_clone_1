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

$mainRepoPath = 'docs/chatgpt_status/height_difference/automation/height_difference_1_official_boundary_and_wcs_v1.py'
$metadataRepoPath = 'docs/chatgpt_status/height_difference/automation/height_difference_1_ea_survey_metadata_v1.py'
$hmlrRepoPath = 'docs/chatgpt_status/height_difference/automation/height_difference_1_hmlr_zip_resolver_v1.py'
$mainScript = Resolve-RepoScript -RepoPath $mainRepoPath -TempName 'height_difference_1_official_boundary_and_wcs_v1.py'
$metadataScript = Resolve-RepoScript -RepoPath $metadataRepoPath -TempName 'height_difference_1_ea_survey_metadata_v1.py'
$hmlrScript = Resolve-RepoScript -RepoPath $hmlrRepoPath -TempName 'height_difference_1_hmlr_zip_resolver_v1.py'

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
  foreach ($line in @($lines)) {
    [Console]::Out.WriteLine([string]$line)
  }
  return [int]$code
}

$runnerOutput = Join-Path $repoRoot 'docs\chatgpt_status\height_difference\shards\height_difference_1\runner_outputs\official_boundary_and_wcs_latest.json'
$metadataOutput = Join-Path $repoRoot 'docs\chatgpt_status\height_difference\shards\height_difference_1\runner_outputs\official_survey_metadata_latest.json'
$hmlrReceipt = Join-Path $repoRoot 'docs\chatgpt_status\height_difference\shards\height_difference_1\runner_outputs\official_hmlr_zip_gml_latest.json'
$websiteOutput = Join-Path $repoRoot 'england_map_web\data\aays_18_slots\height_difference_1\verified_results_latest.json'
$tempMetadataMap = Join-Path ([System.IO.Path]::GetTempPath()) 'height_difference_1_official_survey_metadata_map.json'
$tempGml = Join-Path ([System.IO.Path]::GetTempPath()) 'height_difference_1_barking_dagenham_current.gml'

Write-Output 'SLOT_ID=height_difference_1'
Write-Output 'TASK_VERSION=1.4-hmlr-zip-three-stage-fail-closed'
Write-Output "REPO_ROOT=$repoRoot"
Write-Output "MAIN_SCRIPT=$mainScript"
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

  $mainSelfTest = Invoke-Python -Arguments @($mainScript, '--self-test')
  Write-Output "MAIN_SELF_TEST_EXIT_CODE=$mainSelfTest"
  if ($mainSelfTest -ne 0) { Write-Output 'FINAL_READY=false'; exit $mainSelfTest }

  $hmlrExit = Invoke-Python -Arguments @(
    $hmlrScript,
    '--gml-output', $tempGml,
    '--receipt-output', $hmlrReceipt
  )
  Write-Output "HMLR_ZIP_PYTHON_EXIT_CODE=$hmlrExit"
  if ($hmlrExit -ne 0) { Write-Output 'FINAL_READY=false'; exit $hmlrExit }
  if (-not (Test-Path -LiteralPath $tempGml -PathType Leaf)) { throw 'HMLR_EXTRACTED_GML_MISSING' }
  if (-not (Test-Path -LiteralPath $hmlrReceipt -PathType Leaf)) { throw 'HMLR_ZIP_RECEIPT_MISSING' }
  $hmlrDocument = Get-Content -LiteralPath $hmlrReceipt -Raw -Encoding UTF8 | ConvertFrom-Json
  if ($hmlrDocument.slot_id -ne 'height_difference_1' -or $hmlrDocument.state -ne 'COMPLETED_ZIP_AND_GML_VERIFIED') {
    throw 'HMLR_ZIP_RECEIPT_INVALID'
  }
  Write-Output "HMLR_ZIP_SHA256=$($hmlrDocument.artifacts.hmlr_zip.sha256)"
  Write-Output "HMLR_GML_SHA256=$($hmlrDocument.artifacts.hmlr_gml.sha256)"

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
  if ($metadataDocument.slot_id -ne 'height_difference_1' -or $null -eq $metadataDocument.metadata) {
    throw 'OFFICIAL_SURVEY_METADATA_OUTPUT_INVALID'
  }
  $metadataJson = $metadataDocument.metadata | ConvertTo-Json -Depth 20
  [System.IO.File]::WriteAllText($tempMetadataMap, ($metadataJson + [Environment]::NewLine), [System.Text.UTF8Encoding]::new($false))
  $resolvedRows = @($metadataDocument.metadata.PSObject.Properties).Count
  Write-Output "SURVEY_METADATA_RESOLVED_ROWS=$resolvedRows"

  $gmlUri = ([System.Uri]::new($tempGml)).AbsoluteUri
  $mainExit = Invoke-Python -Arguments @(
    $mainScript,
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
  Remove-Item -LiteralPath $tempMetadataMap -Force -ErrorAction SilentlyContinue
  Remove-Item -LiteralPath $tempGml -Force -ErrorAction SilentlyContinue
}
