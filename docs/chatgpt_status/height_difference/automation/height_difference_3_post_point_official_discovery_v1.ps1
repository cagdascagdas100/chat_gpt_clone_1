[CmdletBinding()]
param(
  [string]$EpochPolicy = $env:AAYS_HD3_EPOCH_POLICY
)
$ErrorActionPreference = 'Stop'
if ([string]::IsNullOrWhiteSpace($EpochPolicy)) { $EpochPolicy = 'UNKNOWN_FAIL_CLOSED' }
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = (& git -C $ScriptDir rev-parse --show-toplevel).Trim()
if (-not $RepoRoot) { throw 'REPO_ROOT_NOT_RESOLVED' }
$PythonScript = Join-Path $RepoRoot 'docs/chatgpt_status/height_difference/automation/height_difference_3_post_point_official_discovery_v1.py'
$CanonicalPoints = Join-Path $RepoRoot 'docs/chatgpt_status/height_difference/runner_outputs/height_difference_3_canonical_points_latest.json'
$Output = Join-Path $RepoRoot 'docs/chatgpt_status/height_difference/runner_outputs/height_difference_3_official_discovery_latest.json'
$RawDir = Join-Path $RepoRoot 'docs/chatgpt_status/height_difference/runner_outputs/height_difference_3_official_discovery_raw'
$WebsiteOutput = Join-Path $RepoRoot 'england_map_web/data/height_difference/height_difference_3_official_discovery_latest.json'
if (-not (Test-Path -LiteralPath $CanonicalPoints)) { throw 'CANONICAL_POINT_OUTPUT_NOT_FOUND' }
$Python = Get-Command python -ErrorAction SilentlyContinue
if (-not $Python) { $Python = Get-Command py -ErrorAction SilentlyContinue }
if (-not $Python) { throw 'PYTHON_NOT_FOUND' }
& $Python.Source $PythonScript --canonical-points $CanonicalPoints --output $Output --raw-dir $RawDir --epoch-policy $EpochPolicy
$ExitCode = $LASTEXITCODE
if (Test-Path -LiteralPath $Output) {
  $WebsiteDir = Split-Path -Parent $WebsiteOutput
  New-Item -ItemType Directory -Force -Path $WebsiteDir | Out-Null
  Copy-Item -LiteralPath $Output -Destination $WebsiteOutput -Force
}
exit $ExitCode
