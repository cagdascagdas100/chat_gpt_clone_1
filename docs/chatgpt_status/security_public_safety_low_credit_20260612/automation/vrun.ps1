$script = Join-Path $PSScriptRoot "security_public_safety_20260619_df_headerfix_wrapper.ps1"
if (-not (Test-Path $script)) { exit 2 }
& $script
if ($null -ne $LASTEXITCODE) { exit $LASTEXITCODE }
exit 0
