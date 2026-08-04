$ErrorActionPreference = 'Stop'
$repoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..\..'))
$implementation = Join-Path $repoRoot 'docs\chatgpt_status\aays1\automation\gas_emissions_2_wave380_ghcr_bottle_layer_tar_member_tabular_suffix_frequency_gate_20260804.py'
$prior = Join-Path $repoRoot 'england_map_web\data\aays_21_slots\gas_emissions_2\wave379_ghcr_bottle_layer_tar_member_geodata_suffix_frequency_gate_20260804.json'
$source = Join-Path $repoRoot 'england_map_web\data\aays_21_slots\gas_emissions_2\wave368_ghcr_bottle_layer_tar_member_path_prefix_gate_20260803.json'
$output = Join-Path $repoRoot 'england_map_web\data\aays_21_slots\gas_emissions_2\wave380_ghcr_bottle_layer_tar_member_tabular_suffix_frequency_gate_20260804.json'
$expectedImplementationSha256 = 'bce78316b4263a1e93aec41a5fec3dbd51491ed8d84509be595ad3b25a7bb66c'
$expectedPriorSha256 = 'ee39f01e2e80cd2f022088a5248173dbf63048c995cafd04e3619aa85949b5a1'
$expectedSourceSha256 = '4a312e00c733ea0a3c1810537445e0c5294bdb3afb62e940a5ca14ceef4ef245'
if (-not (Test-Path -LiteralPath $implementation -PathType Leaf)) { throw 'WAVE380_IMPLEMENTATION_NOT_FOUND' }
if (-not (Test-Path -LiteralPath $prior -PathType Leaf)) { throw 'WAVE379_PRIOR_OUTPUT_NOT_FOUND' }
if (-not (Test-Path -LiteralPath $source -PathType Leaf)) { throw 'WAVE368_SOURCE_OUTPUT_NOT_FOUND' }
if ((Get-FileHash -LiteralPath $implementation -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expectedImplementationSha256) { throw 'WAVE380_IMPLEMENTATION_SHA256_MISMATCH' }
if ((Get-FileHash -LiteralPath $prior -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expectedPriorSha256) { throw 'WAVE379_PRIOR_SHA256_MISMATCH' }
if ((Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expectedSourceSha256) { throw 'WAVE368_SOURCE_SHA256_MISMATCH' }
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) { throw 'PYTHON_NOT_FOUND' }
$accessedAt = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
& $python.Source $implementation --prior $prior --source $source --output $output --accessed-at $accessedAt
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
if (-not (Test-Path -LiteralPath $output -PathType Leaf)) { throw 'WAVE380_OUTPUT_NOT_WRITTEN' }
