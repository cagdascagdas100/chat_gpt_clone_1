$ErrorActionPreference = 'Stop'
$repoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..\..'))
$implementation = Join-Path $repoRoot 'docs\chatgpt_status\aays1\automation\gas_emissions_2_wave384_ghcr_bottle_layer_tar_member_executable_suffix_frequency_gate_20260804.py'
$prior = Join-Path $repoRoot 'england_map_web\data\aays_21_slots\gas_emissions_2\wave383_ghcr_bottle_layer_tar_member_script_suffix_frequency_gate_20260804.json'
$source = Join-Path $repoRoot 'england_map_web\data\aays_21_slots\gas_emissions_2\wave368_ghcr_bottle_layer_tar_member_path_prefix_gate_20260803.json'
$output = Join-Path $repoRoot 'england_map_web\data\aays_21_slots\gas_emissions_2\wave384_ghcr_bottle_layer_tar_member_executable_suffix_frequency_gate_20260804.json'
$expectedImplementationSha256 = '634c18c81e9a2870002700d682b8c48f2de711b95cc2c2af703284c6f6674578'
$expectedPriorSha256 = '2f4390a6500f19f6d99e1313fbb95cc87b5cd2d25bf15a7e4d8a0f2f5d48b74d'
$expectedSourceSha256 = '4a312e00c733ea0a3c1810537445e0c5294bdb3afb62e940a5ca14ceef4ef245'
if (-not (Test-Path -LiteralPath $implementation -PathType Leaf)) { throw 'WAVE384_IMPLEMENTATION_NOT_FOUND' }
if (-not (Test-Path -LiteralPath $prior -PathType Leaf)) { throw 'WAVE383_PRIOR_OUTPUT_NOT_FOUND' }
if (-not (Test-Path -LiteralPath $source -PathType Leaf)) { throw 'WAVE368_SOURCE_OUTPUT_NOT_FOUND' }
if ((Get-FileHash -LiteralPath $implementation -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expectedImplementationSha256) { throw 'WAVE384_IMPLEMENTATION_SHA256_MISMATCH' }
if ((Get-FileHash -LiteralPath $prior -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expectedPriorSha256) { throw 'WAVE383_PRIOR_SHA256_MISMATCH' }
if ((Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expectedSourceSha256) { throw 'WAVE368_SOURCE_SHA256_MISMATCH' }
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) { throw 'PYTHON_NOT_FOUND' }
$accessedAt = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
& $python.Source $implementation --prior $prior --source $source --output $output --accessed-at $accessedAt
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
if (-not (Test-Path -LiteralPath $output -PathType Leaf)) { throw 'WAVE384_OUTPUT_NOT_WRITTEN' }
