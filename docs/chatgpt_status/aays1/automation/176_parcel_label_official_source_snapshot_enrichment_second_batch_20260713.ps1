$ErrorActionPreference = 'Stop'
$repoRoot = if ($env:AAYS_REPO_ROOT) { $env:AAYS_REPO_ROOT } else { (Get-Location).Path }
$repoRoot = [System.IO.Path]::GetFullPath($repoRoot).TrimEnd('\')
$templateRel = 'docs/chatgpt_status/aays1/automation/175_parcel_label_official_source_snapshot_enrichment_20260713.ps1'
$templatePath = Join-Path $repoRoot ($templateRel -replace '/','\')
if (-not (Test-Path -LiteralPath $templatePath)) { throw "missing template automation: $templateRel" }
$scriptText = Get-Content -LiteralPath $templatePath -Raw
$replacements = [ordered]@{
  '175_aays1_parcel_label_official_source_snapshot_enrichment_20260713' = '176_aays1_parcel_label_official_source_snapshot_enrichment_second_batch_20260713'
  '175_distance_property_types_official_source_snapshot_enrichment_20260713.json' = '176_distance_property_types_official_source_snapshot_enrichment_second_batch_20260713.json'
  '175_aays1_parcel_label_official_source_snapshot_enrichment_20260713.task.json' = '176_aays1_parcel_label_official_source_snapshot_enrichment_second_batch_20260713.task.json'
  '175_parcel_label_official_source_snapshot_enrichment_evidence_20260713.json' = '176_parcel_label_official_source_snapshot_enrichment_second_batch_evidence_20260713.json'
  '175_parcel_label_official_source_snapshot_enrichment_report_20260713.md' = '176_parcel_label_official_source_snapshot_enrichment_second_batch_report_20260713.md'
  '175_official_source_snapshots' = '176_official_source_snapshots'
  '175_official_source_snapshot_enrichment_20260713' = '176_official_source_snapshot_enrichment_second_batch_20260713'
  'Task 175' = 'Task 176'
  'task_175_primary_or_authoritative_source_and_address_enrichment' = 'task_176_primary_or_authoritative_source_and_address_enrichment_second_batch'
  "'175_official_source_snapshot_enrichment'" = "'176_official_source_snapshot_enrichment_second_batch'"
  "'175'" = "'176'"
  'selenium_proof_for_task_175_not_generated' = 'selenium_proof_for_task_176_not_generated'
}
foreach ($key in $replacements.Keys) { $scriptText = $scriptText.Replace($key, $replacements[$key]) }
$env:AAYS_TASK_ID = '176_aays1_parcel_label_official_source_snapshot_enrichment_second_batch_20260713'
& ([scriptblock]::Create($scriptText))
