$ErrorActionPreference = 'Stop'

$PageKey = 'gas_emissions'
$TaskId = 'terrayield-088-gas-emissions-proxy-finalize'
$AutomationPath = "docs/chatgpt_status/$PageKey/automation/run_088_proxy_finalize.ps1"
$ReportDir = "docs/chatgpt_status/$PageKey/reports"
$StatusDir = "docs/chatgpt_status/$PageKey/status"
New-Item -ItemType Directory -Force $ReportDir,$StatusDir | Out-Null

$Report = Join-Path $ReportDir "$TaskId.txt"
$StatusFile = Join-Path $StatusDir "$TaskId.txt"
$OutputAcceptanceReport = Join-Path $ReportDir 'terrayield-089-gas-output-acceptance.txt'
$OutputAcceptanceStatus = Join-Path $StatusDir 'terrayield-089-gas-output-acceptance.txt'
$DataContractReport = Join-Path $ReportDir 'terrayield-091-gas-emissions-data-contract-probe.txt'
$DataContractStatus = Join-Path $StatusDir 'terrayield-091-gas-emissions-data-contract-probe.txt'
$FrontendReport = Join-Path $ReportDir 'terrayield-092-gas-emissions-frontend-static-probe.txt'
$FrontendStatus = Join-Path $StatusDir 'terrayield-092-gas-emissions-frontend-static-probe.txt'

$Source = 'england_map_web/data/parcel_air_quality_scores.geojson'
$Output = 'england_map_web/data/parcel_emissions_scores.geojson'
$Frontend = 'england_map_web/app.js'

function Write-Lines($Path, [string[]]$Lines) {
  $dir = Split-Path -Parent $Path
  if ($dir) { New-Item -ItemType Directory -Force $dir | Out-Null }
  $Lines | Set-Content -Encoding UTF8 $Path
}

$rows = @(
  "page_key=$PageKey",
  "task_id=$TaskId",
  "automation_path=$AutomationPath",
  "source=$Source",
  "output=$Output",
  "source_type=air_quality_proxy",
  "fake_data=false",
  "db_write=false",
  "migration=false",
  "production_deploy=false"
)

if (-not (Test-Path $Source)) {
  $rows += 'status=SOURCE_MISSING'
  $rows += 'completion_percent=99'
  $rows += 'final_ready=false'
  Write-Lines $Report $rows
  Write-Lines $StatusFile @('status=SOURCE_MISSING',"report=$Report",'completion_percent=99','final_ready=false')
  exit 2
}

try {
  $src = Get-Content $Source -Raw | ConvertFrom-Json
} catch {
  $rows += 'status=SOURCE_PARSE_FAILED'
  $rows += "error=$($_.Exception.Message)"
  $rows += 'completion_percent=99'
  $rows += 'final_ready=false'
  Write-Lines $Report $rows
  Write-Lines $StatusFile @('status=SOURCE_PARSE_FAILED',"report=$Report",'completion_percent=99','final_ready=false')
  exit 3
}

$outFeatures = @()
foreach ($f in @($src.features)) {
  if ($null -eq $f) { continue }
  $p = $f.properties
  if ($null -eq $p) { $p = [pscustomobject]@{} }
  $v = $null
  foreach ($name in @('pollutionRiskPercent','pollution_risk_percent','risk_percent','air_quality_percent','score')) {
    if ($p.PSObject.Properties.Name -contains $name -and $null -ne $p.$name) {
      $v = [double]$p.$name
      break
    }
  }
  if ($null -eq $v) { $v = 0 }
  if ($v -lt 0) { $v = 0 }
  if ($v -gt 100) { $v = 100 }

  $props = [ordered]@{}
  foreach ($pp in $p.PSObject.Properties) { $props[$pp.Name] = $pp.Value }
  $props['emission_percent'] = [math]::Round($v,2)
  $props['source_type'] = 'air_quality_proxy'
  $props['gas_emissions_note'] = 'Air pollution risk proxy; not official CO2e inventory.'
  $outFeatures += [ordered]@{ type='Feature'; geometry=$f.geometry; properties=$props }
}

$out = [ordered]@{
  type = 'FeatureCollection'
  name = 'parcel_emissions_scores_air_quality_proxy'
  metadata = [ordered]@{
    task_id = $TaskId
    source_type = 'air_quality_proxy'
    source = $Source
    emission_percent_definition = 'emission_percent equals pollutionRiskPercent where available; this is an air pollution risk proxy, not official CO2e/gas inventory.'
    fake_data = $false
    db_write = $false
    migration = $false
    production_deploy = $false
    feature_count = $outFeatures.Count
  }
  features = $outFeatures
}

$out | ConvertTo-Json -Depth 100 | Set-Content -Encoding UTF8 $Output

$outputExists = Test-Path $Output
$featureCount = $outFeatures.Count
$outputOk = $outputExists -and ($featureCount -gt 0)
Write-Lines $OutputAcceptanceReport @(
  'page_key=gas_emissions',
  'task_id=terrayield-089-gas-output-acceptance',
  "output=$Output",
  "output_exists=$outputExists",
  "feature_count=$featureCount",
  "status=$(if ($outputOk) { 'PASS' } else { 'FAIL' })",
  "final_ready=$(if ($outputOk) { 'true' } else { 'false' })"
)
Write-Lines $OutputAcceptanceStatus @("status=$(if ($outputOk) { 'PASS' } else { 'FAIL' })", "report=$OutputAcceptanceReport", "feature_count=$featureCount")

$missingContract = 0
foreach ($f in $outFeatures) {
  if ($null -eq $f.properties.emission_percent -or $null -eq $f.properties.source_type) { $missingContract++ }
}
$contractOk = $outputOk -and ($missingContract -eq 0)
Write-Lines $DataContractReport @(
  'page_key=gas_emissions',
  'task_id=terrayield-091-gas-emissions-data-contract-probe',
  "feature_count=$featureCount",
  "missing_contract_count=$missingContract",
  "required_properties=emission_percent,source_type",
  "status=$(if ($contractOk) { 'PASS' } else { 'FAIL' })",
  "final_ready=$(if ($contractOk) { 'true' } else { 'false' })"
)
Write-Lines $DataContractStatus @("status=$(if ($contractOk) { 'PASS' } else { 'FAIL' })", "report=$DataContractReport", "missing_contract_count=$missingContract")

$tokens = @('gas-emissions-fill','gas-emissions-line','parcel_emissions_scores.geojson','emission_percent','EMISSIONS_CONTROL_MODE','air.png')
$missingTokens = @()
if (Test-Path $Frontend) {
  $frontText = Get-Content $Frontend -Raw
  foreach ($token in $tokens) {
    if ($frontText -notlike "*$token*") { $missingTokens += $token }
  }
} else {
  $missingTokens += 'app.js_missing'
}
$frontendOk = ($missingTokens.Count -eq 0)
Write-Lines $FrontendReport @(
  'page_key=gas_emissions',
  'task_id=terrayield-092-gas-emissions-frontend-static-probe',
  "frontend=$Frontend",
  "required_tokens=$($tokens -join ',')",
  "missing_tokens=$($missingTokens -join ',')",
  "status=$(if ($frontendOk) { 'PASS' } else { 'FAIL' })",
  "final_ready=$(if ($frontendOk) { 'true' } else { 'false' })"
)
Write-Lines $FrontendStatus @("status=$(if ($frontendOk) { 'PASS' } else { 'FAIL' })", "report=$FrontendReport", "missing_tokens=$($missingTokens -join ',')")

$finalReady = $outputOk -and $contractOk -and $frontendOk
$completion = if ($finalReady) { 100 } elseif ($outputOk -and $contractOk) { 96 } elseif ($outputOk) { 92 } else { 99 }
$status = if ($finalReady) { 'FINAL_READY' } elseif ($outputOk -and $contractOk) { 'FRONTEND_ACCEPTANCE_PENDING' } elseif ($outputOk) { 'DATA_CONTRACT_PENDING' } else { 'OUTPUT_EMPTY_OR_MISSING' }

$rows += "status=$status"
$rows += "feature_count=$featureCount"
$rows += "output_acceptance=$(if ($outputOk) { 'PASS' } else { 'FAIL' })"
$rows += "data_contract=$(if ($contractOk) { 'PASS' } else { 'FAIL' })"
$rows += "frontend_static=$(if ($frontendOk) { 'PASS' } else { 'FAIL' })"
$rows += "missing_frontend_tokens=$($missingTokens -join ',')"
$rows += "completion_percent=$completion"
$rows += "final_ready=$(if ($finalReady) { 'true' } else { 'false' })"
Write-Lines $Report $rows
Write-Lines $StatusFile @("status=$status", "report=$Report", "feature_count=$featureCount", "completion_percent=$completion", "final_ready=$(if ($finalReady) { 'true' } else { 'false' })")

if ($finalReady) { exit 0 }
exit 4
