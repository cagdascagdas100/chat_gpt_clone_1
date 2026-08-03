$ErrorActionPreference = 'Stop'
$repoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..\..'))
$implementation = Join-Path $repoRoot 'docs\chatgpt_status\aays1\automation\gas_emissions_2_wave369_ghcr_bottle_layer_tar_member_path_depth_gate_20260803.py'
$prior = Join-Path $repoRoot 'england_map_web\data\aays_21_slots\gas_emissions_2\wave368_ghcr_bottle_layer_tar_member_path_prefix_gate_20260803.json'
$output = Join-Path $repoRoot 'england_map_web\data\aays_21_slots\gas_emissions_2\wave369_ghcr_bottle_layer_tar_member_path_depth_gate_20260803.json'
if (-not (Test-Path -LiteralPath $implementation -PathType Leaf)) { throw 'WAVE369_IMPLEMENTATION_NOT_FOUND' }
if (-not (Test-Path -LiteralPath $prior -PathType Leaf)) { throw 'WAVE368_PRIOR_OUTPUT_NOT_FOUND' }
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) { throw 'PYTHON_NOT_FOUND' }
$accessedAt = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
& $python.Source $implementation --prior $prior --output $output --accessed-at $accessedAt
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
if (-not (Test-Path -LiteralPath $output -PathType Leaf)) { throw 'WAVE369_OUTPUT_NOT_WRITTEN' }
