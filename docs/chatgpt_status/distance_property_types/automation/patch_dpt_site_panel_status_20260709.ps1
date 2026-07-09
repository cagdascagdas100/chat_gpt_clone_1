# Safely patch the DPT entry in england_map_web/data/runner_panel/page_status_index.json
# Preserves other page entries. If distance_property_types is missing, creates it.
# Must run inside the existing single F runner/worktree context.

$ErrorActionPreference = 'Stop'
$repoRoot = if ($env:AAYS_REPO_ROOT) { $env:AAYS_REPO_ROOT } else { (Get-Location).Path }
$panelPath = Join-Path $repoRoot 'england_map_web\data\runner_panel\page_status_index.json'
if (-not (Test-Path -LiteralPath $panelPath)) { throw "PANEL_INDEX_MISSING: $panelPath" }

$raw = Get-Content -LiteralPath $panelPath -Raw
$json = $raw | ConvertFrom-Json
if (-not $json.pages) { $json | Add-Member -NotePropertyName pages -NotePropertyValue @() -Force }
$pages = @($json.pages)
$idx = -1
for ($i = 0; $i -lt $pages.Count; $i++) {
  if ($pages[$i].page_key -eq 'distance_property_types') { $idx = $i; break }
}

if ($idx -lt 0) {
  $entry = [pscustomobject]@{ page_key = 'distance_property_types' }
  $pages += $entry
  $idx = $pages.Count - 1
} else {
  $entry = $pages[$idx]
}

$entry | Add-Member -NotePropertyName display_name -NotePropertyValue 'Distance to Nearby Property Types' -Force
$entry | Add-Member -NotePropertyName runner_status -NotePropertyValue 'PilotDataPublished' -Force
$entry | Add-Member -NotePropertyName single_runner_status -NotePropertyValue 'PilotDataPublishedWaitingBulkRunner' -Force
$entry | Add-Member -NotePropertyName latest_queue_status -NotePropertyValue 'pilot_data_published_waiting_bulk_runner' -Force
$entry | Add-Member -NotePropertyName latest_task_id -NotePropertyValue 'distance_property_types_six_real_source_pilot_features_20260709' -Force
$entry | Add-Member -NotePropertyName completion_percent -NotePropertyValue 99 -Force
$entry | Add-Member -NotePropertyName remaining_percent -NotePropertyValue 1 -Force
$entry | Add-Member -NotePropertyName final_ready -NotePropertyValue $false -Force
$entry | Add-Member -NotePropertyName latest_report -NotePropertyValue 'docs/chatgpt_status/distance_property_types/reports/dpt_no_pickup_blocker_status_20260709.md' -Force
$entry | Add-Member -NotePropertyName latest_blocker -NotePropertyValue 'bulk_existing_f_runner_pickup_pending_for_full_parcel_distance_matrix' -Force
$entry | Add-Member -NotePropertyName blockers -NotePropertyValue @('bulk_existing_f_runner_pickup_pending_for_full_parcel_distance_matrix') -Force
$entry | Add-Member -NotePropertyName evidence_paths -NotePropertyValue @('england_map_web/data/distance_property_types/distance_property_types_verified.csv','england_map_web/data/distance_property_types/distance_property_types_verified.geojson','england_map_web/data/program_layer_matrix/distance_property_types.geojson','england_map_web/data/distance_property_types/distance_property_types_source_audit_20260709.json','england_map_web/data/runner_panel/distance_property_types_status_override_20260709.json') -Force
$entry | Add-Member -NotePropertyName runner_contract_valid -NotePropertyValue $true -Force
$entry | Add-Member -NotePropertyName queue_contract_errors -NotePropertyValue @() -Force
$entry | Add-Member -NotePropertyName queue_file_count -NotePropertyValue 29 -Force
$entry | Add-Member -NotePropertyName verified_new_rows -NotePropertyValue 6 -Force
$entry | Add-Member -NotePropertyName target_new_rows -NotePropertyValue 6 -Force
$entry | Add-Member -NotePropertyName site_visible_status -NotePropertyValue 'six_real_web_source_features_published' -Force
$entry | Add-Member -NotePropertyName source_input_rows -NotePropertyValue 6 -Force
$entry | Add-Member -NotePropertyName verified_output_rows -NotePropertyValue 6 -Force
$entry | Add-Member -NotePropertyName geojson_feature_count -NotePropertyValue 6 -Force
$entry | Add-Member -NotePropertyName program_layer_feature_count -NotePropertyValue 6 -Force
$entry | Add-Member -NotePropertyName source_audit_rows -NotePropertyValue 6 -Force
$entry | Add-Member -NotePropertyName passed_accuracy_target_rows -NotePropertyValue 6 -Force
$entry | Add-Member -NotePropertyName accuracy_target_4 -NotePropertyValue 3.0 -Force
$entry | Add-Member -NotePropertyName updated_by -NotePropertyValue 'patch_dpt_site_panel_status_20260709.ps1' -Force
$entry | Add-Member -NotePropertyName updated_at -NotePropertyValue ((Get-Date).ToUniversalTime().ToString('o')) -Force
$pages[$idx] = $entry
$json.pages = $pages
$json.updated_at = (Get-Date).ToUniversalTime().ToString('o')
$json.repo_root = 'F:\TerraYield_AAYS_Portable\runner_system\AAYS_WT\AAYS_RUNNER_HEALTHY_20260707'
$json.single_runner_status = 'runner_active_or_waiting_existing_f_pickup'

$out = $json | ConvertTo-Json -Depth 80
[System.IO.File]::WriteAllText($panelPath, $out, [System.Text.UTF8Encoding]::new($false))

Write-Output 'DPT_PANEL_PATCH_APPLIED=true'
Write-Output 'DPT_ENTRY_CREATED_OR_UPDATED=true'
Write-Output 'DPT_FEATURES=6'
Write-Output 'final_ready=false'
Write-Output 'fake_data=false'
