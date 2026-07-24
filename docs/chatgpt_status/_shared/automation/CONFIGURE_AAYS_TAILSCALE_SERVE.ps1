[CmdletBinding()]
param()
$ErrorActionPreference = "Stop"
$tailscale = Get-Command tailscale.exe -ErrorAction SilentlyContinue
if (-not $tailscale) { throw "TAILSCALE_NOT_INSTALLED" }
$status = & $tailscale.Source status --json | ConvertFrom-Json
if ($status.BackendState -ne "Running") { throw "TAILSCALE_LOGIN_REQUIRED" }
& $tailscale.Source serve --bg http://127.0.0.1:8012
if ($LASTEXITCODE -ne 0) { throw "TAILSCALE_SERVE_FAILED" }
& $tailscale.Source serve status