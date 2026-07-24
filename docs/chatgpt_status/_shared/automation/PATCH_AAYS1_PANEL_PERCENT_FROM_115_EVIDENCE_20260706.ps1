[CmdletBinding()]
param(
  [string]$RepoRoot = "C:\AAYS_WT\AAYS_REPAIR_20260706_1738"
)

$ErrorActionPreference = "Stop"
if (!(Test-Path -LiteralPath $RepoRoot)) { throw "RepoRoot not found: $RepoRoot" }

$targets = @(
  "docs\chatgpt_status\_shared\panel\page_status_index_latest.json",
  "docs\chatgpt_status\_shared\status\page_panel_index.json",
  "docs\chatgpt_status\_shared\status\pages_status_dashboard.json",
  "england_map_web\data\runner_panel\page_status_index.json"
)

$evidence = "docs/chatgpt_status/aays1/status/115_verified_rows_150_evidence_20260706_1810.json"
$patched = @()
foreach ($rel in $targets) {
  $path = Join-Path $RepoRoot $rel
  if (!(Test-Path -LiteralPath $path)) { continue }
  $obj = Get-Content -LiteralPath $path -Raw | ConvertFrom-Json
  foreach ($p in @($obj.pages)) {
    if ($p.page_key -eq "aays1") {
      $p.completion_percent = 100
      $p.remaining_percent = 0
      $p.final_ready = $false
      $p.runner_status = "Problem"
      $p.latest_queue_status = "done"
      $p.latest_task_id = "security-batch-join-backoff-force-pickup-20260704-0430"
      if ($null -eq $p.evidence_paths) { $p | Add-Member -NotePropertyName evidence_paths -NotePropertyValue @() -Force }
      if (-not (@($p.evidence_paths) -contains $evidence)) { $p.evidence_paths = @($p.evidence_paths) + $evidence }
    }
  }
  $obj.updated_at = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
  $obj.last_checked_at = $obj.updated_at
  [System.IO.File]::WriteAllText($path, ($obj | ConvertTo-Json -Depth 100), [System.Text.UTF8Encoding]::new($false))
  $null = Get-Content -LiteralPath $path -Raw | ConvertFrom-Json
  $patched += $rel
}

$statusDir = Join-Path $RepoRoot "docs\chatgpt_status\_shared\status"
New-Item -ItemType Directory -Force -Path $statusDir | Out-Null
$status = [ordered]@{
  status = "AAYS1_PANEL_PERCENT_PATCH_FROM_115_EVIDENCE"
  patched_files = $patched
  aays1_completion_percent = 100
  aays1_remaining_percent = 0
  final_ready = $false
  note = "Batch 115 panel percent only; product final_ready remains false and shared MULTI_PAGE_latest_status still needs V5 runner sync."
}
[System.IO.File]::WriteAllText((Join-Path $statusDir "aays1_panel_percent_patch_from_115_20260706.json"), ($status | ConvertTo-Json -Depth 20), [System.Text.UTF8Encoding]::new($false))
Write-Output "AAYS1_PANEL_PERCENT_PATCH_FROM_115_EVIDENCE completion=100 remaining=0 final_ready=false"
