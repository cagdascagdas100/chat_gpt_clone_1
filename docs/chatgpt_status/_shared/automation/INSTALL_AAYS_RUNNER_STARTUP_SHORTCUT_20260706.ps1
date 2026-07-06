[CmdletBinding()]
param(
  [string]$ShortcutName = "AAYS Single Runner",
  [switch]$WhatIfOnly
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..\..\..")).Path
$target = Join-Path $repoRoot "START_AAYS_CANONICAL_RUNNER_AND_PANEL.cmd"
$startupDir = [Environment]::GetFolderPath("Startup")
$shortcutPath = Join-Path $startupDir "$ShortcutName.lnk"

if ($WhatIfOnly) {
  [pscustomobject]@{
    would_create = $shortcutPath
    target = $target
  } | ConvertTo-Json -Depth 4
  exit 0
}

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $target
$shortcut.WorkingDirectory = $repoRoot
$shortcut.Description = "Start AAYS canonical single runner and panel"
$shortcut.Save()

[pscustomobject]@{
  created = $shortcutPath
  target = $target
} | ConvertTo-Json -Depth 4
