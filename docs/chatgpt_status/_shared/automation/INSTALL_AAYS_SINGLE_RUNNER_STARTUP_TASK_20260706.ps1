[CmdletBinding()]
param(
  [string]$RepoRoot = "C:\AAYS_WT\AAYS_REPAIR_20260706_1738",
  [ValidateSet("Startup","Desktop")][string]$Location = "Startup",
  [switch]$WhatIfOnly
)

$ErrorActionPreference = "Stop"
$repo = (Resolve-Path -LiteralPath $RepoRoot).Path
$launcher = Join-Path $repo "START_AAYS_SINGLE_RUNNER_PANEL.cmd"
if (-not (Test-Path -LiteralPath $launcher)) { throw "Missing launcher: $launcher" }
$targetDir = if ($Location -eq "Desktop") { [Environment]::GetFolderPath("Desktop") } else { [Environment]::GetFolderPath("Startup") }
$shortcutPath = Join-Path $targetDir "AAYS Single Runner Panel.lnk"
$logDir = Join-Path $repo "docs/chatgpt_status/_shared/logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$logPath = Join-Path $logDir "startup_shortcut_install_20260706.log"
if ($WhatIfOnly) {
  [pscustomobject]@{ would_create=$shortcutPath; target=$launcher; location=$Location } | ConvertTo-Json -Depth 4
  exit 0
}
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $launcher
$shortcut.WorkingDirectory = $repo
$shortcut.Description = "AAYS single shared runner and panel launcher"
$shortcut.Save()
"$(Get-Date -Format o) created_or_updated=$shortcutPath target=$launcher" | Add-Content -LiteralPath $logPath -Encoding UTF8
[pscustomobject]@{ created_or_updated=$shortcutPath; target=$launcher; log=$logPath; idempotent=$true } | ConvertTo-Json -Depth 4
