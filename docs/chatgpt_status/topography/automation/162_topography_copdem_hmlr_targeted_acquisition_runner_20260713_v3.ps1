[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

function Ensure-Dir([string]$Path) {
  if ($Path -and -not (Test-Path -LiteralPath $Path)) {
    New-Item -ItemType Directory -Force -Path $Path | Out-Null
  }
}

$repoRoot = [System.IO.Path]::GetFullPath([string]$env:AAYS_REPO_ROOT)
if (-not $repoRoot -or $repoRoot -notmatch '(?i)[\\/]TerraYield_AAYS_Portable[\\/]runner_system[\\/]') {
  throw 'TOPOGRAPHY_162_V3_REQUIRES_PORTABLE_SHARED_RUNNER_WORKTREE'
}

$sourceRel = 'docs/chatgpt_status/topography/automation/162_topography_copdem_hmlr_targeted_acquisition_runner_20260713_v2.ps1'
$sourcePath = Join-Path $repoRoot ($sourceRel -replace '/', '\')
if (-not (Test-Path -LiteralPath $sourcePath)) {
  throw 'TOPOGRAPHY_162_V2_SOURCE_SCRIPT_MISSING'
}

$cursor = $repoRoot
while ($cursor -and (Split-Path -Leaf $cursor) -ne 'runner_system') {
  $parent = Split-Path -Parent $cursor
  if (-not $parent -or $parent -eq $cursor) { break }
  $cursor = $parent
}
if ((Split-Path -Leaf $cursor) -ne 'runner_system') {
  throw 'TOPOGRAPHY_162_V3_RUNNER_SYSTEM_ROOT_NOT_FOUND'
}

$portableRoot = Split-Path -Parent $cursor
$tempRoot = Join-Path $portableRoot '_portable_logs\temp'
Ensure-Dir $tempRoot
$tempScript = Join-Path $tempRoot ('topography_162_v3_' + [guid]::NewGuid().ToString('N') + '.ps1')

$source = Get-Content -LiteralPath $sourcePath -Raw -Encoding UTF8
$broken = "-replace'\','/'"
$fixed = ".Replace('\','/')"
if (-not $source.Contains($broken)) {
  throw 'TOPOGRAPHY_162_V3_EXPECTED_INVALID_REGEX_FRAGMENT_NOT_FOUND'
}
$patched = $source.Replace($broken, $fixed)
[System.IO.File]::WriteAllText($tempScript, $patched, [System.Text.UTF8Encoding]::new($false))

try {
  & powershell -NoProfile -ExecutionPolicy Bypass -File $tempScript
  $exitCode = $LASTEXITCODE
  if ($null -eq $exitCode) { $exitCode = 0 }
  if ($exitCode -ne 0) {
    throw "TOPOGRAPHY_162_V3_INNER_EXIT_CODE_$exitCode"
  }
} finally {
  Remove-Item -LiteralPath $tempScript -Force -ErrorAction SilentlyContinue
}
