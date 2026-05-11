$ErrorActionPreference = "Stop"
$TaskId = "terrayield-048-future-growth-stage2-connector-spec-retry"
$Root = "C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence"
Set-Location $Root
Write-Output "PROJECT=terrayield"
Write-Output "DISPLAY_PROJECT=TerraYield"
Write-Output "CHATGPT_PAGE_PROJECT=aays1"
Write-Output ("TASK=" + $TaskId)
Write-Output "MODE=stage2_connector_spec_retry_minimal_diff"
$RegistryPath = Join-Path $Root "FG_STAGE1_SOURCE_REGISTRY.csv"
$Target = Join-Path $Root "FG_STAGE2_CONNECTOR_SPEC.md"
if (!(Test-Path $RegistryPath)) { Write-Output "FAILED=missing_stage1_registry"; exit 1 }
$Registry = Import-Csv $RegistryPath
$Lines = New-Object System.Collections.Generic.List[string]
$Lines.Add("# Connector Spec - Future Growth Layer")
$Lines.Add("")
$Lines.Add("## Scope Guard")
$Lines.Add("- layer_name: Future Urban Growth & Value Shift Layer")
$Lines.Add("- calculation_version: future_growth_v1")
$Lines.Add("- disclaimer_required: ""Kesin fiyat tahmini değildir""")
$Lines.Add("- confidence_guard: source_url olmayan kayıt high confidence olamaz")
$Lines.Add("- evidence_guard: popup evidence sadece ilgili parsel ile spatial olarak eşleşmiş kayıtları gösterebilir")
$Lines.Add("")
$Lines.Add("## Normalized Target Shape")
$Lines.Add("- target_table: future_growth_features")
$Lines.Add("- required_fields:")
$Lines.Add("  - source_key")
$Lines.Add("  - source_url")
$Lines.Add("  - feature_type")
$Lines.Add("  - external_id")
$Lines.Add("  - idempotency_key")
$Lines.Add("  - geometry")
$Lines.Add("  - centroid")
$Lines.Add("  - geography_level")
$Lines.Add("  - effective_date")
$Lines.Add("  - observed_date")
$Lines.Add("  - raw_payload_ref")
$Lines.Add("  - mode")
$Lines.Add("  - confidence_cap_reason")
$Lines.Add("- allowed_modes: live, fixture, stub")
$Lines.Add("- confidence_rule: live kaynak + source_url + parsel-specific spatial match olmadan high confidence üretilemez")
$Lines.Add("- confidence_rule: fixture ve stub kayıtlar production-compatible typed shape taşır ancak high confidence üretmez")
$Lines.Add("")
foreach ($Row in $Registry) {
  $SourceKey = [string]$Row.source_key
  $Mode = [string]$Row.mode
  $Purpose = [string]$Row.purpose
  $Geography = [string]$Row.geography
  $SourceUrl = [string]$Row.source_url
  if ([string]::IsNullOrWhiteSpace($SourceUrl)) { Write-Output ("FAILED=missing_source_url:" + $SourceKey); exit 1 }
  $Lines.Add("---")
  $Lines.Add("")
  $Lines.Add("## Connector Spec - " + $SourceKey)
  $Lines.Add("- source_key: " + $SourceKey)
  $Lines.Add("- source_name: " + $Row.source_name)
  $Lines.Add("- source_url: " + $SourceUrl)
  $Lines.Add("- mode: " + $Mode)
  $Lines.Add("- purpose: " + $Purpose)
  $Lines.Add("- geography: " + $Geography)
  $Lines.Add("- input_schema:")
  $Lines.Add("  - format: typed " + $Mode + " payload compatible with future_growth_features")
  $Lines.Add("  - required_fields: source_key, source_url, external_id, observed_date, mode")
  $Lines.Add("  - geometry_fields: geometry and centroid when source geography supports spatial matching")
  $Lines.Add("- normalized_output_map:")
  $Lines.Add("  - feature_type: " + $Purpose)
  $Lines.Add("  - external_id: source-native stable identifier or deterministic fixture/stub identifier")
  $Lines.Add("  - geometry: source geometry when available; otherwise null typed placeholder")
  $Lines.Add("  - centroid: derived from geometry when available; otherwise null typed placeholder")
  $Lines.Add("  - geography_level: " + $Geography)
  $Lines.Add("  - effective_date: source effective date when available")
  $Lines.Add("  - observed_date: ingestion run date or fixture generation date")
  $Lines.Add("  - raw_payload_ref: stable pointer to raw source row, fixture row, or stub payload")
  $Lines.Add("  - mode: " + $Mode)
  $Lines.Add("  - confidence_cap_reason: high confidence disabled unless source_url and parcel-specific spatial match both exist")
  $Lines.Add("- idempotency_key:")
  $Lines.Add("  - rule: " + $SourceKey + ":external_id:observed_date")
  $Lines.Add("- failure_handling:")
  $Lines.Add("  - missing_source_url: reject record")
  $Lines.Add("  - malformed_payload: reject affected record and keep previous successful snapshot when available")
  $Lines.Add("  - missing_geometry: disable parcel popup evidence unless a typed matcher resolves parcel-specific geometry")
  $Lines.Add("  - source_unavailable: use fixture/stub mode with the same typed output shape")
  $Lines.Add("  - confidence_fallback: cap below high unless source_url and parcel-specific spatial match both exist")
  $Lines.Add("")
}
Set-Content -Path $Target -Value $Lines -Encoding UTF8
Write-Output "VALIDATION=started"
$ConnectorCount = (Select-String -Path $Target -Pattern "^## Connector Spec - ").Count
$InputSchemaCount = (Select-String -Path $Target -Pattern "^- input_schema:").Count
$OutputMapCount = (Select-String -Path $Target -Pattern "^- normalized_output_map:").Count
$IdempotencyCount = (Select-String -Path $Target -Pattern "^- idempotency_key:").Count
$FailureHandlingCount = (Select-String -Path $Target -Pattern "^- failure_handling:").Count
$SourceUrlCount = (Select-String -Path $Target -Pattern "^- source_url: https?://").Count
$TodoMatches = @(Select-String -Path $Target -Pattern "TODO" -ErrorAction SilentlyContinue)
Write-Output ("CONNECTOR_COUNT=" + $ConnectorCount)
Write-Output ("INPUT_SCHEMA_COUNT=" + $InputSchemaCount)
Write-Output ("OUTPUT_MAP_COUNT=" + $OutputMapCount)
Write-Output ("IDEMPOTENCY_COUNT=" + $IdempotencyCount)
Write-Output ("FAILURE_HANDLING_COUNT=" + $FailureHandlingCount)
Write-Output ("SOURCE_URL_COUNT=" + $SourceUrlCount)
Write-Output ("TODO_COUNT=" + $TodoMatches.Count)
if ($ConnectorCount -lt 16) { Write-Output "FAILED=connector_count_below_stage1_registry"; exit 1 }
if ($InputSchemaCount -lt 16 -or $OutputMapCount -lt 16 -or $IdempotencyCount -lt 16 -or $FailureHandlingCount -lt 16) { Write-Output "FAILED=missing_required_connector_section"; exit 1 }
if ($SourceUrlCount -lt 16) { Write-Output "FAILED=missing_source_url"; exit 1 }
if ($TodoMatches.Count -gt 0) { Write-Output "FAILED=todo_not_allowed"; exit 1 }
Select-String -Path $Target -Pattern "calculation_version: future_growth_v1" | Out-String | Write-Output
Select-String -Path $Target -Pattern "Kesin fiyat tahmini değildir" | Out-String | Write-Output
Select-String -Path $Target -Pattern "source_url olmayan kayıt high confidence olamaz" | Out-String | Write-Output
Write-Output "VALIDATION=passed"
git diff -- FG_STAGE2_CONNECTOR_SPEC.md 2>&1 | Out-String | Write-Output
Write-Output "TERRAYIELD_STAGE2_DONE"
exit 0
