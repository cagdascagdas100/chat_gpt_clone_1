$ErrorActionPreference = 'Stop'
$repoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..\..'))
$implementation = Join-Path $repoRoot 'docs\chatgpt_status\aays1\automation\gas_emissions_2_wave377_ghcr_bottle_layer_tar_member_compression_suffix_frequency_gate_20260804.py'
$prior = Join-Path $repoRoot 'england_map_web\data\aays_21_slots\gas_emissions_2\wave376_ghcr_bottle_layer_tar_member_compound_extension_frequency_gate_20260804.json'
$source = Join-Path $repoRoot 'england_map_web\data\aays_21_slots\gas_emissions_2\wave368_ghcr_bottle_layer_tar_member_path_prefix_gate_20260803.json'
$output = Join-Path $repoRoot 'england_map_web\data\aays_21_slots\gas_emissions_2\wave377_ghcr_bottle_layer_tar_member_compression_suffix_frequency_gate_20260804.json'
$expectedImplementationSha256 = '6404c2e83b94aacc5255a49a192c80caab30f3cea1a012f7a2d2efd0c040ca2a'
$expectedPriorSha256 = '31a1fc6a500a17ffe024c1584c6a19f05ec18a97d74e0de3b0fa72e5d1168c90'
$expectedSourceSha256 = '4a312e00c733ea0a3c1810537445e0c5294bdb3afb62e940a5ca14ceef4ef245'
if (-not (Test-Path -LiteralPath $implementation -PathType Leaf)) { throw 'WAVE377_IMPLEMENTATION_NOT_FOUND' }
if (-not (Test-Path -LiteralPath $prior -PathType Leaf)) { throw 'WAVE376_PRIOR_OUTPUT_NOT_FOUND' }
if (-not (Test-Path -LiteralPath $source -PathType Leaf)) { throw 'WAVE368_SOURCE_OUTPUT_NOT_FOUND' }
if ((Get-FileHash -LiteralPath $implementation -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expectedImplementationSha256) { throw 'WAVE377_IMPLEMENTATION_SHA256_MISMATCH' }
if ((Get-FileHash -LiteralPath $prior -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expectedPriorSha256) { throw 'WAVE376_PRIOR_SHA256_MISMATCH' }
if ((Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expectedSourceSha256) { throw 'WAVE368_SOURCE_SHA256_MISMATCH' }
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) { throw 'PYTHON_NOT_FOUND' }
$accessedAt = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
& $python.Source $implementation --prior $prior --source $source --output $output --accessed-at $accessedAt
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
if (-not (Test-Path -LiteralPath $output -PathType Leaf)) { throw 'WAVE377_OUTPUT_NOT_WRITTEN' }
