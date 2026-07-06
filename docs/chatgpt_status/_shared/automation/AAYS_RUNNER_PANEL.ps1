[CmdletBinding()]
param(
  [switch]$Console
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..\..\..")).Path
$builder = Join-Path $PSScriptRoot "BUILD_AAYS_PAGE_PANEL_INDEX.ps1"
$indexPath = Join-Path $repoRoot "docs/chatgpt_status/_shared/panel/page_status_index_latest.json"

function Refresh-Index {
  & powershell -NoProfile -ExecutionPolicy Bypass -File $builder -RepoRoot $repoRoot -EnsurePageDirs | Out-Null
  if (Test-Path -LiteralPath $indexPath) {
    return Get-Content -Raw -LiteralPath $indexPath | ConvertFrom-Json
  }
  return $null
}

function Get-PanelRows {
  $index = Refresh-Index
  if ($null -eq $index) { return @() }
  $priority = @{
    "auto-1.4-readyToSell" = 1
    "auto-3.5-parcelLabel" = 2
    "auto-6.7-security" = 3
    "auto-5.6-gasEmission" = 4
    "auto-4.6-heightDifferance" = 5
  }
  return @($index.pages | Sort-Object @{
    Expression = {
      if ($priority.ContainsKey($_.display_name)) { $priority[$_.display_name] } else { 1000 }
    }
  }, page_key)
}

if ($Console) {
  Get-PanelRows | Select-Object display_name,page_key,runner_status,completion_percent,remaining_percent,final_ready,latest_task_id,latest_blocker,last_heartbeat_at | Format-Table -AutoSize
  exit 0
}

try {
  Add-Type -AssemblyName System.Windows.Forms
  Add-Type -AssemblyName System.Drawing
} catch {
  Get-PanelRows | Select-Object display_name,page_key,runner_status,completion_percent,remaining_percent,final_ready,latest_task_id,latest_blocker,last_heartbeat_at | Format-Table -AutoSize
  exit 0
}

$form = New-Object System.Windows.Forms.Form
$form.Text = "AAYS Single Shared Runner Panel"
$form.Width = 1280
$form.Height = 720
$form.StartPosition = "CenterScreen"

$grid = New-Object System.Windows.Forms.DataGridView
$grid.Dock = "Fill"
$grid.ReadOnly = $true
$grid.AllowUserToAddRows = $false
$grid.AllowUserToDeleteRows = $false
$grid.AutoSizeColumnsMode = "Fill"
$grid.SelectionMode = "FullRowSelect"
$grid.RowHeadersVisible = $false

$columns = @(
  "display_name",
  "page_key",
  "runner_status",
  "completion_percent",
  "remaining_percent",
  "final_ready",
  "latest_task_id",
  "latest_queue_task",
  "latest_report",
  "last_heartbeat_at",
  "latest_blocker"
)
foreach ($column in $columns) {
  [void]$grid.Columns.Add($column, $column)
}

function Update-Grid {
  $grid.Rows.Clear()
  foreach ($row in Get-PanelRows) {
    $idx = $grid.Rows.Add(
      [string]$row.display_name,
      [string]$row.page_key,
      [string]$row.runner_status,
      [string]$row.completion_percent,
      [string]$row.remaining_percent,
      [string]$row.final_ready,
      [string]$row.latest_task_id,
      [string]$row.latest_queue_task,
      [string]$row.latest_report,
      [string]$row.last_heartbeat_at,
      [string]$row.latest_blocker
    )
    $gridRow = $grid.Rows[$idx]
    switch ([string]$row.runner_status) {
      "Runner Aktif" { $gridRow.DefaultCellStyle.BackColor = [System.Drawing.Color]::FromArgb(224, 245, 232) }
      "Problem" { $gridRow.DefaultCellStyle.BackColor = [System.Drawing.Color]::FromArgb(255, 226, 226) }
      "Bekliyor" { $gridRow.DefaultCellStyle.BackColor = [System.Drawing.Color]::FromArgb(255, 246, 204) }
      "Calisiyor" { $gridRow.DefaultCellStyle.BackColor = [System.Drawing.Color]::FromArgb(224, 239, 255) }
      default { $gridRow.DefaultCellStyle.BackColor = [System.Drawing.Color]::White }
    }
  }
}

$timer = New-Object System.Windows.Forms.Timer
$timer.Interval = 30000
$timer.Add_Tick({ Update-Grid })

$form.Controls.Add($grid)
$form.Add_Shown({
  Update-Grid
  $timer.Start()
})
$form.Add_FormClosing({ $timer.Stop() })

[void]$form.ShowDialog()
