$ErrorActionPreference = 'Stop'
$repoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..\..'))
$implementation = Join-Path $repoRoot 'docs\chatgpt_status\aays1\automation\gas_emissions_2_wave374_ghcr_bottle_layer_tar_member_suffix_chain_frequency_gate_20260803.py'
$prior = Join-Path $repoRoot 'england_map_web\data\aays_21_slots\gas_emissions_2\wave373_ghcr_bottle_layer_tar_member_stem_frequency_gate_20260803.json'
$source = Join-Path $repoRoot 'england_map_web\data\aays_21_slots\gas_emissions_2\wave368_ghcr_bottle_layer_tar_member_path_prefix_gate_20260803.json'
$output = Join-Path $repoRoot 'england_map_web\data\aays_21_slots\gas_emissions_2\wave374_ghcr_bottle_layer_tar_member_suffix_chain_frequency_gate_20260803.json'
$expectedImplementationSha256 = '24c8d1731312ca69fbf2af6f29a5d076fa689d32f94ea99c7aaba9d86c5ee8ef'
$expectedPriorSha256 = '55f4f4d15d8388ef4e8aafb46a0f03bf7bc0ca66306a9225068ca0e341a6b2eb'
$expectedSourceSha256 = '4a312e00c733ea0a3c1810537445e0c5294bdb3afb62e940a5ca14ceef4ef245'
if (-not (Test-Path -LiteralPath $implementation -PathType Leaf)) { throw 'WAVE374_IMPLEMENTATION_NOT_FOUND' }
if (-not (Test-Path -LiteralPath $prior -PathType Leaf)) { throw 'WAVE373_PRIOR_OUTPUT_NOT_FOUND' }
if (-not (Test-Path -LiteralPath $source -PathType Leaf)) { throw 'WAVE368_SOURCE_OUTPUT_NOT_FOUND' }
if ((Get-FileHash -LiteralPath $implementation -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expectedImplementationSha256) { throw 'WAVE374_IMPLEMENTATION_SHA256_MISMATCH' }
if ((Get-FileHash -LiteralPath $prior -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expectedPriorSha256) { throw 'WAVE373_PRIOR_SHA256_MISMATCH' }
if ((Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expectedSourceSha256) { throw 'WAVE368_SOURCE_SHA256_MISMATCH' }
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) { throw 'PYTHON_NOT_FOUND' }
$accessedAt = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
& $python.Source $implementation --prior $prior --source $source --output $output --accessed-at $accessedAt
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
if (-not (Test-Path -LiteralPath $output -PathType Leaf)) { throw 'WAVE374_OUTPUT_NOT_WRITTEN' }
