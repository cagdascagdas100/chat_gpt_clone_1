$script = Join-Path $PSScriptRoot "security_public_safety_20260619_df_headerfix_wrapper.ps1"
if (Test-Path $script) { & $script; exit 0 }
exit 0
