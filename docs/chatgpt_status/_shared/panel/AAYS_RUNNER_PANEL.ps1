[CmdletBinding()]
param(
  [string]$RepoRoot = "",
  [switch]$Console
)

$ErrorActionPreference = "Stop"
if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
  $RepoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..\..")).Path
} else {
  $RepoRoot = (Resolve-Path -LiteralPath $RepoRoot).Path
}

$sharedRoot = Join-Path $RepoRoot "docs/chatgpt_status/_shared"
$builder = Join-Path $sharedRoot "automation/BUILD_AAYS_PAGE_PANEL_INDEX.ps1"
$indexPath = Join-Path $sharedRoot "panel/page_status_index_latest.json"
$configCandidates = @(
  (Join-Path $sharedRoot "panel/PANEL_MENU_CONFIG.json"),
  (Join-Path $sharedRoot "panel/panel_menu_config.json")
)

function First-Value {
  foreach ($value in $args) {
    if ($null -ne $value -and -not [string]::IsNullOrWhiteSpace([string]$value)) { return $value }
  }
  return $null
}
function Read-JsonFile {
  param([string]$Path)
  if (-not (Test-Path -LiteralPath $Path)) { return $null }
  try { return Get-Content -Raw -LiteralPath $Path | ConvertFrom-Json -ErrorAction Stop } catch { return $null }
}

function Refresh-Index {
  if (Test-Path -LiteralPath $builder) {
    & powershell -NoProfile -ExecutionPolicy Bypass -File $builder -RepoRoot $RepoRoot -EnsurePageDirs | Out-Null
  }
  return Read-JsonFile -Path $indexPath
}

function Get-PanelConfig {
  foreach ($candidate in $configCandidates) {
    $config = Read-JsonFile -Path $candidate
    if ($null -ne $config -and $null -ne $config.menus) { return $config }
  }
  return [pscustomobject]@{ menus = @() }
}

function Get-RunnerLabel {
  param($Index)
  if ($null -eq $Index) { return "RUNNER PANEL INDEX YOK" }
  $blockers = New-Object System.Collections.Generic.List[string]
  foreach ($page in @($Index.pages)) {
    foreach ($blocker in @($page.blockers)) {
      if (-not [string]::IsNullOrWhiteSpace([string]$blocker)) { $blockers.Add([string]$blocker) }
    }
    if (-not [string]::IsNullOrWhiteSpace([string]$page.latest_blocker)) { $blockers.Add([string]$page.latest_blocker) }
  }
  if ($blockers.Count -gt 0) { return "RUNNER BLOCKED" }
  if ([bool]$Index.single_runner_active -or [string]$Index.single_runner_status -eq "active") { return "RUNNER AKTIF" }
  if ([string]$Index.single_runner_status -match "stale") { return "RUNNER STALE" }
  return "RUNNER CALISMIYOR"
}

function Get-Rows {
  param($Index)
  if ($null -eq $Index -or $null -eq $Index.pages) { return @() }
  return @($Index.pages | Sort-Object page_key)
}

if ($Console) {
  $index = Refresh-Index
  $config = Get-PanelConfig
  [pscustomobject]@{
    runner_status = Get-RunnerLabel -Index $index
    menu_count = @($config.menus).Count
    updated_at = if ($null -ne $index) { $index.updated_at } else { $null }
    repo_root = $RepoRoot
  } | Format-List
  Get-Rows -Index $index | Select-Object page_key,runner_status,completion_percent,final_ready,latest_task_id,latest_queue_status,last_heartbeat_at,latest_blocker | Format-Table -AutoSize
  exit 0
}

try {
  Add-Type -AssemblyName System.Windows.Forms
  Add-Type -AssemblyName System.Drawing
} catch {
  $index = Refresh-Index
  Get-Rows -Index $index | Select-Object page_key,runner_status,completion_percent,final_ready,latest_task_id,latest_blocker | Format-Table -AutoSize
  exit 0
}

$form = New-Object System.Windows.Forms.Form
$form.Text = "AAYS Single Shared Runner Panel"
$form.Width = 1320
$form.Height = 760
$form.StartPosition = "CenterScreen"

$menuStrip = New-Object System.Windows.Forms.MenuStrip
$statusLabel = New-Object System.Windows.Forms.ToolStripLabel
$statusLabel.Text = "RUNNER STATUS: loading"
[void]$menuStrip.Items.Add($statusLabel)

function Load-MenusIntoStrip {
  $config = Get-PanelConfig
  while ($menuStrip.Items.Count -gt 1) { $menuStrip.Items.RemoveAt(1) }
  foreach ($menu in @($config.menus | Select-Object -First 5)) {
    $item = New-Object System.Windows.Forms.ToolStripMenuItem
    $item.Name = [string]$menu.id
    $item.Text = [string]$menu.label
    $item.ToolTipText = "Configured in docs/chatgpt_status/_shared/panel/PANEL_MENU_CONFIG.json"
    [void]$menuStrip.Items.Add($item)
  }
}

$grid = New-Object System.Windows.Forms.DataGridView
$grid.Dock = "Fill"
$grid.ReadOnly = $true
$grid.AllowUserToAddRows = $false
$grid.AllowUserToDeleteRows = $false
$grid.AutoSizeColumnsMode = "Fill"
$grid.SelectionMode = "FullRowSelect"
$grid.RowHeadersVisible = $false

$columns = @("page_key", "status", "percent", "queue", "task_id", "heartbeat", "push", "final_ready", "safety", "blocker")
foreach ($column in $columns) { [void]$grid.Columns.Add($column, $column) }

function Update-Grid {
  Load-MenusIntoStrip
  $index = Refresh-Index
  $runnerLabel = Get-RunnerLabel -Index $index
  $statusLabel.Text = "RUNNER STATUS: $runnerLabel"
  if ($runnerLabel -eq "RUNNER AKTIF") { $statusLabel.ForeColor = [System.Drawing.Color]::FromArgb(0, 100, 40) }
  elseif ($runnerLabel -match "BLOCKED|STALE|YOK") { $statusLabel.ForeColor = [System.Drawing.Color]::FromArgb(170, 30, 30) }
  else { $statusLabel.ForeColor = [System.Drawing.Color]::FromArgb(120, 85, 0) }

  $grid.Rows.Clear()
  foreach ($row in Get-Rows -Index $index) {
    $safety = "fake=$($row.fake_data) db=$($row.db_write) migration=$($row.migration) prod=$($row.production_deploy)"
    $blocker = [string]$row.latest_blocker
    if ([string]::IsNullOrWhiteSpace($blocker)) { $blocker = (@($row.blockers) -join "; ") }
    $idx = $grid.Rows.Add(
      [string]$row.page_key,
      [string](First-Value $row.runner_status $row.single_runner_status),
      [string]$row.completion_percent,
      [string]$row.latest_queue_status,
      [string]$row.latest_task_id,
      [string](First-Value $row.last_heartbeat_at $row.heartbeat_at),
      [string](First-Value $row.PUSH_SYNC_OK $row.push_sync_ok "unknown"),
      [string]$row.final_ready,
      $safety,
      $blocker
    )
    $gridRow = $grid.Rows[$idx]
    $statusText = ([string]$row.runner_status + " " + $blocker).ToLowerInvariant()
    if ($statusText -match "problem|blocked|missing|error") { $gridRow.DefaultCellStyle.BackColor = [System.Drawing.Color]::FromArgb(255, 226, 226) }
    elseif ($statusText -match "aktif|active|completed|done") { $gridRow.DefaultCellStyle.BackColor = [System.Drawing.Color]::FromArgb(224, 245, 232) }
    else { $gridRow.DefaultCellStyle.BackColor = [System.Drawing.Color]::FromArgb(255, 246, 204) }
  }
}

$timer = New-Object System.Windows.Forms.Timer
$timer.Interval = 30000
$timer.Add_Tick({ Update-Grid })

$form.MainMenuStrip = $menuStrip
$form.Controls.Add($grid)
$form.Controls.Add($menuStrip)
$form.Add_Shown({ Update-Grid; $timer.Start() })
$form.Add_FormClosing({ $timer.Stop() })

[void]$form.ShowDialog()
