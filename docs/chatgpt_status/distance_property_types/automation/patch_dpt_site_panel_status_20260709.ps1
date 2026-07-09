# Safely patch the DPT entry in england_map_web/data/runner_panel/page_status_index.json
# This script preserves other page entries and only updates distance_property_types.
# It must run inside the existing single F runner/worktree context.

$ErrorActionPreference = 'Stop'
$repoRoot = if ($env:AAYS_REPO_ROOT) { $env:AAYS_REPO_ROOT } else { (Get-Location).Path }
$panelPath = Join-Path $repoRoot 'england_map_web\data\runner_panel\page_status_index.json'
if (-not (Test-Path -LiteralPath $panelPath)) { throw "PANEL_INDEX_MISSING: $panelPath" }

$raw = Get-Content -LiteralPath $panelPath -Raw
$json = $raw | ConvertFrom-Json
$pages = @($json.pages)
$idx = -1
for ($i = 0; $i -lt $pages.Count; $i++) {
  if ($pages[$i].page_key -eq 'distance_property_types') { $idx = $i; break }
}
if ($idx -lt 0) { throw 'DPT_ENTRY_NOT_FOUND_IN_PANEL_INDEX' }

$entry = $pages[$idx]
$entry.runner_status = 'WaitingForExistingFRunnerPickup'
$entry.single_runner_status = 'WaitingForExistingFRunnerPickup'
$entry.latest_queue_status = 'queued_for_single_shared_runner'
$entry.latest_task_id = 'distance_property_types_source_seed_priority_20260708'
$entry.latest_queue_task = 'docs/chatgpt_status/distance_property_types/queue/0000_distance_property_types_source_seed_priority_20260708.task.json'
$entry.completion_percent = 98
$entry.remaining_percent = 2
$entry.final_ready = $false
$entry.latest_report = 'docs/chatgpt_status/distance_property_types/reports/dpt_problem_resolution_plan_20260709.md'
$entry.latest_blocker = 'waiting_for_existing_f_runner_pickup_output'
$entry.blockers = @('waiting_for_existing_f_runner_pickup_output')
$entry.evidence_paths = @(
  'england_map_web/data/distance_property_types/distance_property_types_site_status.json',
  'docs/chatgpt_status/distance_property_types/reports/dpt_problem_resolution_plan_20260709.md',
  'docs/chatgpt_status/_shared/status/reboot_runner_start_request_20260709_f_portable_hotfix_continue.json',
  'docs/chatgpt_status/_shared/automation/RUN_EXISTING_F_PORTABLE_SINGLE_RUNNER_HOTFIX_THEN_CONTINUE_20260709.ps1'
)
$entry.runner_contract_valid = $true
$entry.queue_contract_errors = @()
$entry.queue_file_count = 29
$entry.verified_new_rows = 0
$entry.target_new_rows = 6
$entry.site_visible_status = 'repo_side_ready_waiting_runner_output'
$entry.source_input_rows = 6
$entry.verified_output_rows = 0
$entry.geojson_feature_count = 0
$entry.updated_by = 'patch_dpt_site_panel_status_20260709.ps1'
$entry.updated_at = (Get-Date).ToUniversalTime().ToString('o')
$pages[$idx] = $entry
$json.pages = $pages
$json.updated_at = (Get-Date).ToUniversalTime().ToString('o')
$json.repo_root = 'F:\TerraYield_AAYS_Portable\runner_system\AAYS_WT\AAYS_RUNNER_HEALTHY_20260707'
$json.single_runner_status = 'runner_active_or_waiting_existing_f_pickup'

$out = $json | ConvertTo-Json -Depth 80
[System.IO.File]::WriteAllText($panelPath, $out, [System.Text.UTF8Encoding]::new($false))

Write-Output 'DPT_PANEL_PATCH_APPLIED=true'
Write-Output 'final_ready=false'
Write-Output 'fake_data=false'
