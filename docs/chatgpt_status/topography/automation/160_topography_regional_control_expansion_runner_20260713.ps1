[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$repoRoot = [System.IO.Path]::GetFullPath([string]$env:AAYS_REPO_ROOT)
if (-not $repoRoot -or $repoRoot -notmatch '(?i)[\\/]TerraYield_AAYS_Portable[\\/]runner_system[\\/]') {
  throw 'TOPOGRAPHY_160_WRAPPER_REQUIRES_PORTABLE_SHARED_RUNNER_WORKTREE'
}

$source = Join-Path $repoRoot 'docs\chatgpt_status\topography\automation\160_topography_regional_control_expansion_20260713.ps1'
if (-not (Test-Path -LiteralPath $source)) { throw 'TOPOGRAPHY_160_SOURCE_SCRIPT_MISSING' }

$text = Get-Content -LiteralPath $source -Raw -Encoding UTF8
$text = $text.Replace("-Status (if (`$check.reachable) { 'source_check_only_available' } else { 'blocked_or_unavailable' })", "-Status `$(if (`$check.reachable) { 'source_check_only_available' } else { 'blocked_or_unavailable' })")
$text = $text.Replace("-Blocker (if (`$check.reachable) { '' } else { `$check.error })", "-Blocker `$(if (`$check.reachable) { '' } else { `$check.error })")

$portableCursor = $repoRoot
while ($portableCursor -and (Split-Path -Leaf $portableCursor) -ne 'runner_system') {
  $parent = Split-Path -Parent $portableCursor
  if ($parent -eq $portableCursor) { break }
  $portableCursor = $parent
}
if ((Split-Path -Leaf $portableCursor) -ne 'runner_system') { throw 'TOPOGRAPHY_160_PORTABLE_ROOT_NOT_RESOLVED' }
$tempRoot = Join-Path (Split-Path -Parent $portableCursor) '_portable_logs\temp'
if (-not (Test-Path -LiteralPath $tempRoot)) { New-Item -ItemType Directory -Force -Path $tempRoot | Out-Null }
$tempScript = Join-Path $tempRoot ('topography_160_' + [guid]::NewGuid().ToString('N') + '.ps1')
[System.IO.File]::WriteAllText($tempScript, $text, [System.Text.UTF8Encoding]::new($false))
try {
  & powershell -NoProfile -ExecutionPolicy Bypass -File $tempScript
  if ($LASTEXITCODE -ne 0) { throw "TOPOGRAPHY_160_EXIT_CODE_$LASTEXITCODE" }
} finally {
  Remove-Item -LiteralPath $tempScript -Force -ErrorAction SilentlyContinue
}
