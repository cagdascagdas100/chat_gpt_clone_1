[CmdletBinding()]
param([string]$RepoRoot = "")
$ErrorActionPreference = "Stop"
if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
  $RepoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..\..\..")).Path
}
function JP([string]$p) { Join-Path $RepoRoot $p }
function RJ([string]$p) { Get-Content -Raw -LiteralPath (JP $p) | ConvertFrom-Json -ErrorAction Stop }
function WJ([string]$p, [object]$v) { $v | ConvertTo-Json -Depth 100 | Set-Content -LiteralPath (JP $p) -Encoding UTF8 }
function Set-JsonProp($o,[string]$n,$v) { if ($null -eq $o.PSObject.Properties[$n]) { $o | Add-Member -NotePropertyName $n -NotePropertyValue $v } else { $o.PSObject.Properties[$n].Value = $v } }
$ov = RJ "docs/chatgpt_status/_shared/panel/aays1_115_completed_latest.json"
$paths = @(
  "docs/chatgpt_status/_shared/panel/page_status_index_latest.json",
  "docs/chatgpt_status/_shared/status/page_panel_index.json",
  "docs/chatgpt_status/_shared/status/pages_status_dashboard.json",
  "england_map_web/data/runner_panel/page_status_index.json"
)
$evidence = @($ov.runner_output, $ov.manifest, $ov.verified_csv, "docs/chatgpt_status/aays1/queue/0000_115_security_batch_join_backoff_force_pickup.task.json")
$count = 0
foreach ($p in $paths) {
  if (-not (Test-Path -LiteralPath (JP $p))) { continue }
  $idx = RJ $p
  foreach ($pg in @($idx.pages)) {
    if ([string]$pg.page_key -ne "aays1") { continue }
    Set-JsonProp $pg "runner_status" "CompletedEvidence"
    Set-JsonProp $pg "single_runner_status" "CompletedEvidence"
    Set-JsonProp $pg "latest_queue_status" "done"
    Set-JsonProp $pg "completion_percent" 100
    Set-JsonProp $pg "remaining_percent" 0
    Set-JsonProp $pg "latest_blocker" ""
    Set-JsonProp $pg "blockers" @()
    Set-JsonProp $pg "evidence_paths" $evidence
    Set-JsonProp $pg "verified_new_rows" ([int]$ov.verified_new_rows)
    Set-JsonProp $pg "target_new_rows" ([int]$ov.target_new_rows)
    Set-JsonProp $pg "final_ready" $false
    $count++
  }
    Set-JsonProp $idx "updated_at" ((Get-Date).ToUniversalTime().ToString("o"))
  WJ $p $idx
}
$sum = [ordered]@{ page_key="aays1"; status="panel_patch_completed"; patched_entries=$count; final_ready=$false }
WJ "docs/chatgpt_status/_shared/panel/aays1_panel_patch_summary_20260706.json" $sum
Write-Output "PATCHED=$count"
exit 0
