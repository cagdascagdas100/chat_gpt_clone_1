param(
  [string]$RepoRoot = (Get-Location).Path
)

$ErrorActionPreference = 'Stop'
$datasetUrl = 'https://assets.publishing.service.gov.uk/media/68653c7ee6c3cc924228943f/2005-23-uk-local-authority-ghg-emissions-CSV-dataset.csv'
$outDir = Join-Path $RepoRoot 'outputs/england_program_parcel_matrix_20260629/gas_emissions_updates'
$evidenceDir = Join-Path $RepoRoot 'docs/chatgpt_status/gas_emissions/evidence'
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
New-Item -ItemType Directory -Force -Path $evidenceDir | Out-Null

$csvPath = Join-Path $evidenceDir '2005-23-uk-local-authority-ghg-emissions-CSV-dataset.csv'
if (-not (Test-Path $csvPath)) {
  Invoke-WebRequest -Uri $datasetUrl -OutFile $csvPath -UseBasicParsing
}

$targetAuthority = 'Barking and Dagenham'
$sample = Get-Content -Path $csvPath -TotalCount 1
$headers = $sample -split ','
$rows = Import-Csv -Path $csvPath
$matched = $rows | Where-Object {
  ($_.PSObject.Properties.Value -contains $targetAuthority) -or
  (($_.PSObject.Properties | Where-Object { [string]$_.Value -like '*Barking*Dagenham*' }).Count -gt 0)
}

if (-not $matched -or $matched.Count -eq 0) {
  throw 'No official Barking and Dagenham rows found in GOV.UK GHG CSV.'
}

$verifiedPath = Join-Path $outDir 'verified_source_backed_rows_govuk_ghg_20260708.csv'
$matched | Export-Csv -Path $verifiedPath -NoTypeInformation -Encoding UTF8

$status = [ordered]@{
  layer = 'Gas Emissions'
  status = 'OFFICIAL_SOURCE_ROWS_EXTRACTED_REVIEW_REQUIRED'
  fake_data = $false
  source_dataset_gate_passed = $true
  source_row_gate_passed = $true
  final_ready = $false
  manual_review_required = $true
  source = 'GOV.UK DESNZ local authority and regional greenhouse gas emissions statistics 2005 to 2023'
  source_url = $datasetUrl
  target_authority = $targetAuthority
  verified_rows_path = 'outputs/england_program_parcel_matrix_20260629/gas_emissions_updates/verified_source_backed_rows_govuk_ghg_20260708.csv'
  extracted_row_count = @($matched).Count
  updated_at = (Get-Date).ToUniversalTime().ToString('s') + 'Z'
}
$status | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 (Join-Path $outDir 'source_rows_extraction_status_latest.json')
Write-Host "GAS_EMISSIONS_SOURCE_ROWS_EXTRACTED count=$(@($matched).Count) path=$verifiedPath"
