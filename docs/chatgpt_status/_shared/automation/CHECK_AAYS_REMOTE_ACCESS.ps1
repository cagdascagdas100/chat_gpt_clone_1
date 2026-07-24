[CmdletBinding()]
param()
$ErrorActionPreference = "SilentlyContinue"
$root = [IO.Path]::GetFullPath($PSScriptRoot).TrimEnd("")
$state = Join-Path $root "stateemote_access_preflight_latest.json"
$tailscale = Get-Command tailscale.exe -ErrorAction SilentlyContinue
$chromeService = Get-Service -Name chromoting -ErrorAction SilentlyContinue
$tailscaleService = Get-Service -Name Tailscale -ErrorAction SilentlyContinue
$health = $null
try { $health = (Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:8012/health" -TimeoutSec 5).StatusCode } catch {}
$tailscaleStatus = $null
if ($tailscale) { $tailscaleStatus = (& $tailscale.Source status --json 2>$null | ConvertFrom-Json) }
$result = [ordered]@{
  status = if ($chromeService -and $tailscaleService -and $health -eq 200) { "READY" } else { "SETUP_REQUIRED" }
  chrome_remote_desktop_installed = [bool]$chromeService
  chrome_remote_desktop_running = [bool]($chromeService.Status -eq "Running")
  tailscale_installed = [bool]$tailscale
  tailscale_service_running = [bool]($tailscaleService.Status -eq "Running")
  tailscale_backend_state = $tailscaleStatus.BackendState
  tailscale_dns_name = $tailscaleStatus.Self.DNSName
  local_app_health_http = $health
  public_router_port_required = $false
  manual_login_required = -not ($chromeService -and $tailscaleStatus.BackendState -eq "Running")
  checked_at = (Get-Date).ToUniversalTime().ToString("o")
  final_ready = $false
}
[IO.Directory]::CreateDirectory((Split-Path $state)) | Out-Null
[IO.File]::WriteAllText($state, ($result | ConvertTo-Json -Depth 8), (New-Object Text.UTF8Encoding($false)))
$result | ConvertTo-Json -Depth 8