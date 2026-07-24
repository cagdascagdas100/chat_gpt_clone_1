[CmdletBinding()]
param(
  [string]$PortableRoot = "",
  [string]$AutomationRoot = $PSScriptRoot
)

$ErrorActionPreference = "Stop"
if ([string]::IsNullOrWhiteSpace($PortableRoot)) {
  $PortableRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot "..\..\..\..\..\..\.."))
}
$PortableRoot = [System.IO.Path]::GetFullPath($PortableRoot).TrimEnd("\")
$AutomationRoot = [System.IO.Path]::GetFullPath($AutomationRoot).TrimEnd("\")

$identity = Join-Path $PortableRoot ".aays_portable_identity.json"
if (-not (Test-Path -LiteralPath $identity -PathType Leaf)) {
  throw "PORTABLE_IDENTITY_MISSING: $identity"
}
$identityData = Get-Content -LiteralPath $identity -Raw | ConvertFrom-Json
if ($identityData.portable_product -ne "AAYS_TerraYield" -or [int]$identityData.architecture_version -ne 3) {
  throw "PORTABLE_IDENTITY_INVALID_OR_UNSUPPORTED"
}

$files = @(
  @{ Source = "AAYS_ADAPTIVE_15_WORKER_COORDINATOR_ORIGINAL.py"; Destination = "AAYS_ADAPTIVE_15_WORKER_COORDINATOR.py" },
  @{ Source = "AAYS_21_SLOT_RECOVERY_SUPERVISOR.py"; Destination = "AAYS_21_SLOT_RECOVERY_SUPERVISOR.py" },
  @{ Source = "AAYS_RUNNER_KEEPALIVE_WATCHDOG.py"; Destination = "AAYS_RUNNER_KEEPALIVE_WATCHDOG.py" },
  @{ Source = "START_AAYS_RUNNER_KEEPALIVE.ps1"; Destination = "START_AAYS_RUNNER_KEEPALIVE.ps1" },
  @{ Source = "AAYS_PORTABLE_CONTROL_PANEL.py"; Destination = "AAYS_PORTABLE_CONTROL_PANEL.py" },
  @{ Source = "RUN_AAYS_ADAPTIVE_15_WORKER.ps1"; Destination = "RUN_AAYS_ADAPTIVE_15_WORKER.ps1" },
  @{ Source = "..\AAYS_TEK_PARAGRAF_DEVAM_PROMPTU_TR.txt"; Destination = "AAYS_TEK_PARAGRAF_DEVAM_PROMPTU_TR.txt" },
  @{ Source = "..\AAYS_21_SLOT_AYRINTILI_DEVAM_SOZLESMESI_TR.md"; Destination = "AAYS_21_SLOT_AYRINTILI_DEVAM_SOZLESMESI_TR.md" }
)
$backupRoot = Join-Path $PortableRoot ("runtime\adaptive_v2\auto_recovery_backup_" + [DateTime]::UtcNow.ToString("yyyyMMdd_HHmmss"))
New-Item -ItemType Directory -Force -Path $backupRoot | Out-Null

$installed = @()
foreach ($file in $files) {
  $source = Join-Path $AutomationRoot $file.Source
  $destination = Join-Path $PortableRoot $file.Destination
  if (-not (Test-Path -LiteralPath $source -PathType Leaf)) {
    throw "INSTALL_SOURCE_MISSING: $source"
  }
  if (Test-Path -LiteralPath $destination -PathType Leaf) {
    Copy-Item -LiteralPath $destination -Destination (Join-Path $backupRoot $file.Destination) -Force
  }
  $temporary = $destination + ".installing"
  Copy-Item -LiteralPath $source -Destination $temporary -Force
  if ((Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash -ne (Get-FileHash -LiteralPath $temporary -Algorithm SHA256).Hash) {
    throw "INSTALL_HASH_MISMATCH: $($file.Destination)"
  }
  Move-Item -LiteralPath $temporary -Destination $destination -Force
  $installed += $file.Destination
}

[ordered]@{
  status = "PASS"
  portable_root = $PortableRoot
  installed = $installed
  backup_root = $backupRoot
  logical_slots = 21
  automatic_recovery = $true
  restart_required = $true
} | ConvertTo-Json -Depth 5
