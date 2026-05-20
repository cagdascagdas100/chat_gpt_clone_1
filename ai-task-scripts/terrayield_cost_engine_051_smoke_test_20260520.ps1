$ErrorActionPreference = 'Stop'

$BridgeRoot = if ($env:AAYS_BRIDGE_ROOT) { $env:AAYS_BRIDGE_ROOT } else { Split-Path -Parent $PSScriptRoot }
$EngineDir = Join-Path $BridgeRoot 'terrayield_cost_engine\python_demo'
$EnginePy = Join-Path $EngineDir 'terrayield_cost_engine_demo.py'
$InputDir = Join-Path $EngineDir 'sample_inputs'
$ResultRoot = Join-Path $BridgeRoot 'ai-results\terrayield_cost_engine'
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$RunDir = Join-Path $ResultRoot ('run_' + $Stamp)

New-Item -ItemType Directory -Force -Path $InputDir,$RunDir | Out-Null

if (-not (Test-Path $EnginePy)) {
  throw "Engine file not found: $EnginePy"
}

$DetachedInput = Join-Path $InputDir 'detached_london_250m2.json'
if (-not (Test-Path $DetachedInput)) {
@'
{
  "building_type": "Müstakil Ev",
  "subtype": "One-off detached house",
  "location": "London",
  "floors": 2,
  "gia_m2": 250,
  "spec": "Mid",
  "dwelling_units": 1,
  "retail_ratio": 0.0,
  "residential_ratio": 1.0,
  "upfront_pct": 0.20,
  "payment_months": 18,
  "include_land": false,
  "land_cost": 0.0,
  "vat_treatment": "new_qualifying_dwelling"
}
'@ | Set-Content -Encoding UTF8 $DetachedInput
}

$IndustrialInput = Join-Path $RunDir 'industrial_demo_input.json'
@'
{
  "building_type": "Sanayi",
  "subtype": "Food & drink factory",
  "location": "London",
  "floors": 1,
  "gia_m2": 2500,
  "spec": "Mid",
  "dwelling_units": 0,
  "retail_ratio": 0.0,
  "residential_ratio": 0.0,
  "upfront_pct": 0.20,
  "payment_months": 18,
  "include_land": false,
  "land_cost": 0.0,
  "vat_treatment": "standard_20"
}
'@ | Set-Content -Encoding UTF8 $IndustrialInput

$DetachedOut = Join-Path $RunDir 'output_detached_london_250m2.json'
$IndustrialOut = Join-Path $RunDir 'output_industrial_demo_2500m2.json'

Push-Location $EngineDir
try {
  python $EnginePy --input-json $DetachedInput --output-json $DetachedOut
  python $EnginePy --input-json $IndustrialInput --output-json $IndustrialOut
} finally {
  Pop-Location
}

$DetachedJson = Get-Content -Raw -Encoding UTF8 $DetachedOut | ConvertFrom-Json
$IndustrialJson = Get-Content -Raw -Encoding UTF8 $IndustrialOut | ConvertFrom-Json

$SummaryPath = Join-Path $RunDir 'summary.md'
$lines = @(
  '# TerraYield Cost Engine Step 051 Smoke Test',
  '',
  ('Time: ' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss')),
  '',
  '## Detached London 250m2',
  ('Min total GBP: ' + $DetachedJson.totals.min_total_gbp),
  ('Max total GBP: ' + $DetachedJson.totals.max_total_gbp),
  ('Mid total GBP: ' + $DetachedJson.totals.mid_total_gbp),
  ('Initial payment GBP: ' + $DetachedJson.totals.initial_payment_gbp),
  ('Recurring monthly GBP: ' + $DetachedJson.totals.recurring_payment_gbp_per_month),
  ('Line count: ' + $DetachedJson.lines.Count),
  '',
  '## Industrial demo 2500m2',
  ('Min total GBP: ' + $IndustrialJson.totals.min_total_gbp),
  ('Max total GBP: ' + $IndustrialJson.totals.max_total_gbp),
  ('Mid total GBP: ' + $IndustrialJson.totals.mid_total_gbp),
  ('Initial payment GBP: ' + $IndustrialJson.totals.initial_payment_gbp),
  ('Recurring monthly GBP: ' + $IndustrialJson.totals.recurring_payment_gbp_per_month),
  ('Line count: ' + $IndustrialJson.lines.Count),
  '',
  '## Output files',
  ('Detached output: ' + $DetachedOut),
  ('Industrial output: ' + $IndustrialOut),
  '',
  '## Status',
  'OK - Python cost engine smoke test completed.'
)
Set-Content -Encoding UTF8 -Path $SummaryPath -Value $lines

Write-Host "OK TerraYield cost engine smoke test completed"
Write-Host "RunDir=$RunDir"
Write-Host "DetachedMidTotal=$($DetachedJson.totals.mid_total_gbp)"
Write-Host "IndustrialMidTotal=$($IndustrialJson.totals.mid_total_gbp)"
