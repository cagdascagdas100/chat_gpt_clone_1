$ErrorActionPreference = 'Continue'
$TaskId = 'contractor-001-england-groups-scaffold-20260519'
$BridgeRoot = 'C:\AAYS_GITHUB_BRIDGE_CLEAN'
$ContractorRoot = 'E:\AAYS_DATA\contractor'
$ExportDir = Join-Path $ContractorRoot 'exports'
$ManifestDir = Join-Path $ContractorRoot 'manifests'
$CuratedDir = Join-Path $ContractorRoot 'curated'
$RawDir = Join-Path $ContractorRoot 'raw'
$StagingDir = Join-Path $ContractorRoot 'staging'
$ResultDir = Join-Path $BridgeRoot 'ai-results'
New-Item -ItemType Directory -Force -Path $ExportDir,$ManifestDir,$CuratedDir,$RawDir,$StagingDir,$ResultDir | Out-Null
function Step($m){ Write-Output ('[' + (Get-Date -Format s) + '] ' + $m) }
Step "TASK=$TaskId"
Step "CONTRACTOR_ROOT=$ContractorRoot"
# Approximate England analysis grid only. Real parcel IDs are matched later by spatial intersection / authority-postcode proxy.
$minLon = -6.42; $maxLon = 1.78; $minLat = 49.85; $maxLat = 55.85
$cols = 20; $rows = 10
$dx = ($maxLon - $minLon) / $cols
$dy = ($maxLat - $minLat) / $rows
$groups = @()
$idx = 1
for($r=0; $r -lt $rows; $r++){
  for($c=0; $c -lt $cols; $c++){
    $west = [Math]::Round($minLon + ($c*$dx), 6)
    $east = [Math]::Round($minLon + (($c+1)*$dx), 6)
    $south = [Math]::Round($minLat + ($r*$dy), 6)
    $north = [Math]::Round($minLat + (($r+1)*$dy), 6)
    $centLon = [Math]::Round(($west+$east)/2, 6)
    $centLat = [Math]::Round(($south+$north)/2, 6)
    $gid = ('ENG-G{0:D3}' -f $idx)
    $groups += [pscustomobject]@{
      parcel_group_id = $gid
      country = 'England'
      group_method = 'approx_grid_20x10_bbox'
      row_index = $r + 1
      col_index = $c + 1
      min_lon = $west
      min_lat = $south
      max_lon = $east
      max_lat = $north
      centroid_lon = $centLon
      centroid_lat = $centLat
      parcel_id_list = ''
      match_key = $gid
      notes = 'Approximate analysis group. Replace/augment by real parcel geometry intersection later.'
    }
    $idx++
  }
}
$groupsCsv = Join-Path $ExportDir 'england_parcel_groups_200.csv'
$groupsJson = Join-Path $ExportDir 'england_parcel_groups_200.json'
$groups | Export-Csv -NoTypeInformation -Encoding UTF8 -Path $groupsCsv
$groups | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 -Path $groupsJson
$columns = @('contractor_id','entity_type','contractor_name','company_number','officer_or_contact_name','phone','email','website','registered_address','operating_address','postcode','local_authority','service_area_text','source_names','source_urls','source_record_ids','fetched_at','license_names','past_work_summary','past_work_sources','reliability_score_10','identity_accuracy_4','contact_accuracy_4','address_accuracy_4','past_work_accuracy_4','coverage_accuracy_4','overall_accuracy_4','legal_contact_score','quality_band','do_not_contact','covered_parcel_group_ids','matched_parcel_ids','match_method','match_score_10','sort_score','notes')
$template = Join-Path $ExportDir 'contractor_rows_template.csv'
($columns -join ',') | Set-Content -Encoding UTF8 -Path $template
$matchColumns = @('parcel_group_id','contractor_id','contractor_name','coverage_source','coverage_method','evidence_source_url','match_score_10','evidence_score_4','rank_in_group','show_in_app','matched_real_parcel_ids','notes')
$matchTemplate = Join-Path $ExportDir 'contractor_group_match_template.csv'
($matchColumns -join ',') | Set-Content -Encoding UTF8 -Path $matchTemplate
$manifest = [ordered]@{
  task_id = $TaskId
  generated_at = (Get-Date -Format s)
  contractor_root = $ContractorRoot
  outputs = [ordered]@{
    england_parcel_groups_csv = $groupsCsv
    england_parcel_groups_json = $groupsJson
    contractor_rows_template_csv = $template
    contractor_group_match_template_csv = $matchTemplate
  }
  group_count = $groups.Count
  status = 'scaffold_generated_no_fake_contractors'
  next_steps = @('collect_official_sources','normalize_contractors','score_reliability_and_accuracy','match_contractors_to_groups','later_join_real_parcel_ids')
}
$manifestPath = Join-Path $ManifestDir 'contractor_001_england_groups_manifest.json'
$manifest | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 -Path $manifestPath
$report = @()
$report += '# Contractor 001 England Groups Scaffold'
$report += ''
$report += "Generated: $(Get-Date -Format s)"
$report += "Task: $TaskId"
$report += ''
$report += '## Outputs'
$report += "- $groupsCsv"
$report += "- $groupsJson"
$report += "- $template"
$report += "- $matchTemplate"
$report += "- $manifestPath"
$report += ''
$report += '## Grouping'
$report += '- England approximate grid: 20 columns x 10 rows = 200 groups.'
$report += '- Real TerraYield parcel IDs are not present in this page. matched_parcel_ids is intentionally blank until app parcel geometries/IDs are joined.'
$report += ''
$report += '## Contractor data policy'
$report += '- No fake contractor rows generated.'
$report += '- Contractor rows must come from official/legal sources with provenance.'
$report += '- Phone/email/web fields remain blank unless verified from allowed sources or contractor-owned/public contact pages.'
$report += ''
$report += 'TASK_COMPLETION=100/100'
$report += 'TERRAYIELD_TASK_DONE'
$reportPath = Join-Path $ResultDir ($TaskId + '.report.md')
$report | Set-Content -Encoding UTF8 -Path $reportPath
Step "GROUPS_CSV=$groupsCsv"
Step "GROUPS_JSON=$groupsJson"
Step "CONTRACTOR_TEMPLATE=$template"
Step "MATCH_TEMPLATE=$matchTemplate"
Step "MANIFEST=$manifestPath"
Step "REPORT_PATH=$reportPath"
Step 'TASK_COMPLETION=100/100'
Step 'TERRAYIELD_TASK_DONE'
exit 0
