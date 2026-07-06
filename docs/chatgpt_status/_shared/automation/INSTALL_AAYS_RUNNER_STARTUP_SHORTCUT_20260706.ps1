[CmdletBinding()]
param(
  [string]$RepoRoot = "",
  [ValidateSet("Startup", "Desktop")]
  [string]$Location = "Startup",
  [string]$ShortcutName = "AAYS Single Runner Panel",
  [switch]$WhatIfOnly
)

$ErrorActionPreference = "Stop"
if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
  $RepoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..\..\..")).Path
} else {
  $RepoRoot = (Resolve-Path -LiteralPath $RepoRoot).Path
}

$target = Join-Path $RepoRoot "START_AAYS_SINGLE_RUNNER_PANEL.cmd"
if (-not (Test-Path -LiteralPath $target)) {
  throw "Missing single runner launcher: $target"
}

$targetDir = if ($Location -eq "Desktop") {
  [Environment]::GetFolderPath("DesktopDirectory")
} else {
  [Environment]::GetFolderPath("Startup")
}
$shortcutPath = Join-Path $targetDir "$ShortcutName.lnk"
$logDir = Join-Path $RepoRoot "docs/chatgpt_status/_shared/logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

$result = [ordered]@{
  generated_at = (Get-Date).ToUniversalTime().ToString("o")
  location = $Location
  shortcut_path = $shortcutPath
  target = $target
  working_directory = $RepoRoot
  single_runner_lock_enforced_by = "docs/chatgpt_status/_shared/automation/START_AAYS_SINGLE_RUNNER_WITH_PANEL_20260706.ps1"
  creates_parallel_runner = $false
  what_if_only = [bool]$WhatIfOnly
}

if (-not $WhatIfOnly) {
  $shell = New-Object -ComObject WScript.Shell
  $link = $shell.CreateShortcut($shortcutPath)
  $link.TargetPath = $target
  $link.WorkingDirectory = $RepoRoot
  $link.Description = "AAYS single shared runner and visible panel"
  $link.Save()
  $result.created = $true
} else {
  $result.created = $false
}

$result | ConvertTo-Json -Depth 6 | Tee-Object -FilePath (Join-Path $logDir "startup_shortcut_install_latest.json")
