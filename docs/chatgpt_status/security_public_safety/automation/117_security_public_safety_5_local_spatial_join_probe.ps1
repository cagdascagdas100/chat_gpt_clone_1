$ErrorActionPreference = 'Stop'
$Repo = $env:AAYS_REPO_ROOT
if ([string]::IsNullOrWhiteSpace($Repo)) { $Repo = (git rev-parse --show-toplevel).Trim() }
$Py = Join-Path $Repo 'docs\chatgpt_status\security_public_safety\automation\117_security_public_safety_5_local_spatial_join_probe.py'
if (-not (Test-Path -LiteralPath $Py)) { throw "Probe script missing: $Py" }
& python $Py
if ($LASTEXITCODE -ne 0) { throw "Python probe failed with exit code $LASTEXITCODE" }
