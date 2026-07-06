[CmdletBinding()]
param(
  [string]$RepoRoot = "C:\AAYS_WT\AAYS_REPAIR_20260706_1738",
  [ValidateSet("head","incoming")][string]$Side = "incoming"
)

$ErrorActionPreference = "Stop"
if (!(Test-Path -LiteralPath $RepoRoot)) { throw "RepoRoot not found: $RepoRoot" }

function Resolve-Text($text, $side) {
  $lines = $text -split "`r?`n"
  $out = @()
  $mode = "normal"
  foreach ($line in $lines) {
    if ($line.StartsWith("<<<<<<<")) { $mode = "head"; continue }
    if ($line.StartsWith("=======")) { $mode = "incoming"; continue }
    if ($line.StartsWith(">>>>>>>")) { $mode = "normal"; continue }
    if ($mode -eq "normal" -or $mode -eq $side) { $out += $line }
  }
  return ($out -join "`n")
}

$files = @(
  "docs\chatgpt_status\_shared\panel\page_status_index_latest.json",
  "docs\chatgpt_status\_shared\status\page_panel_index.json",
  "docs\chatgpt_status\_shared\status\pages_status_dashboard.json",
  "england_map_web\data\runner_panel\page_status_index.json"
)

$fixed = @()
foreach ($rel in $files) {
  $path = Join-Path $RepoRoot $rel
  if (!(Test-Path -LiteralPath $path)) { continue }
  $raw = Get-Content -LiteralPath $path -Raw
  if ($raw -notmatch "<<<<<<<|=======|>>>>>>>") { continue }
  $clean = Resolve-Text $raw $Side
  $obj = $clean | ConvertFrom-Json
  $json = $obj | ConvertTo-Json -Depth 100
  [System.IO.File]::WriteAllText($path, $json, [System.Text.UTF8Encoding]::new($false))
  $null = Get-Content -LiteralPath $path -Raw | ConvertFrom-Json
  $fixed += $rel
}

$statusDir = Join-Path $RepoRoot "docs\chatgpt_status\_shared\status"
New-Item -ItemType Directory -Force -Path $statusDir | Out-Null
$statusPath = Join-Path $statusDir "panel_json_conflicts_fixed_20260706.json"
[System.IO.File]::WriteAllText($statusPath, (@{ status="fixed"; files=$fixed; final_ready=$false } | ConvertTo-Json -Depth 20), [System.Text.UTF8Encoding]::new($false))
Write-Output "PANEL_JSON_CONFLICTS_FIXED files=$($fixed -join ',') final_ready=false"
