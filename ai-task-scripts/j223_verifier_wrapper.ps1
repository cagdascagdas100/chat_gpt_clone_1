$ErrorActionPreference = 'Stop'
$Script = Join-Path $PSScriptRoot 'terrayield_159_final_verifier_treeaware.ps1'
& $Script
exit $LASTEXITCODE
