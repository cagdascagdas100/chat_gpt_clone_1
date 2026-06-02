$ErrorActionPreference = 'Continue'

$TaskId = 'terrayield-cost-engine-052-robust-smoke-test-20260520'
$BridgeRoot = if ($env:AAYS_BRIDGE_ROOT) { $env:AAYS_BRIDGE_ROOT } else { Split-Path -Parent $PSScriptRoot }
$EngineDir = Join-Path $BridgeRoot 'terrayield_cost_engine\python_demo'
$EnginePy = Join-Path $EngineDir 'terrayield_cost_engine_demo.py'
$ResultRoot = Join-Path $BridgeRoot 'ai-results\terrayield_cost_engine'
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$RunDir = Join-Path $ResultRoot ('run_' + $Stamp + '_052')
$SummaryPath = Join-Path $RunDir 'summary.md'
$StatusPath = Join-Path $RunDir 'status.json'
New-Item -ItemType Directory -Force -Path $RunDir | Out-Null

function Add-Line([string]$Text) { Add-Content -Encoding UTF8 -Path $SummaryPath -Value $Text }
function Write-Status($obj) { $obj | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 -Path $StatusPath }

Set-Content -Encoding UTF8 -Path $SummaryPath -Value @('# TerraYield Cost Engine Step 052 Robust Smoke Test','',('Time: ' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss')),'')
Add-Line ('BridgeRoot: ' + $BridgeRoot)
Add-Line ('EngineDir: ' + $EngineDir)
Add-Line ('EnginePy: ' + $EnginePy)
Add-Line ''

if (-not (Test-Path $EnginePy)) {
  Add-Line '## Status'
  Add-Line 'FAILED - engine file not found.'
  Add-Line ''
  Add-Line '## Directory listing'
  if (Test-Path $EngineDir) {
    Get-ChildItem -Path $EngineDir -Recurse -ErrorAction SilentlyContinue | Select-Object FullName | ForEach-Object { Add-Line $_.FullName }
  } else {
    Add-Line 'EngineDir does not exist.'
  }
  Write-Status ([ordered]@{ task_id=$TaskId; status='failed'; reason='engine_file_not_found'; bridge_root=$BridgeRoot; engine_py=$EnginePy; generated_at=(Get-Date -Format s) })
  Write-Output 'FAILED engine file not found'
  exit 1
}

$PythonCandidates = @()
$cmdPy = Get-Command py -ErrorAction SilentlyContinue
if ($cmdPy) { $PythonCandidates += @('py','-3') }
$cmdPython = Get-Command python -ErrorAction SilentlyContinue
if ($cmdPython) { $PythonCandidates += @('python') }
$cmdPython3 = Get-Command python3 -ErrorAction SilentlyContinue
if ($cmdPython3) { $PythonCandidates += @('python3') }

if ($PythonCandidates.Count -eq 0) {
  Add-Line '## Status'
  Add-Line 'FAILED - Python executable not found in PATH.'
  Write-Status ([ordered]@{ task_id=$TaskId; status='failed'; reason='python_not_found'; bridge_root=$BridgeRoot; generated_at=(Get-Date -Format s) })
  Write-Output 'FAILED python not found'
  exit 2
}

$InputDetached = Join-Path $RunDir 'input_detached_london_250m2.json'
$InputIndustrial = Join-Path $RunDir 'input_industrial_food_factory_2500m2.json'
$OutDetached = Join-Path $RunDir 'output_detached_london_250m2.json'
$OutIndustrial = Join-Path $RunDir 'output_industrial_food_factory_2500m2.json'

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
'@ | Set-Content -Encoding UTF8 $InputDetached

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
'@ | Set-Content -Encoding UTF8 $InputIndustrial

function Invoke-PythonEngine([string]$InputPath, [string]$OutputPath) {
  $ok = $false
  $lastOutput = ''
  $lastExit = 999
  $candidates = @(
    @{exe='py'; args=@('-3')},
    @{exe='python'; args=@()},
    @{exe='python3'; args=@()}
  )
  foreach ($c in $candidates) {
    $found = Get-Command $c.exe -ErrorAction SilentlyContinue
    if (-not $found) { continue }
    Push-Location $EngineDir
    try {
      $cmdArgs = @() + $c.args + @($EnginePy, '--input-json', $InputPath, '--output-json', $OutputPath)
      $lastOutput = (& $c.exe @cmdArgs 2>&1 | Out-String)
      $lastExit = if ($null -ne $LASTEXITCODE) { [int]$LASTEXITCODE } else { 0 }
    } catch {
      $lastOutput = $_.Exception.Message
      $lastExit = 998
    } finally {
      Pop-Location
    }
    Add-Line ('Python candidate: ' + $c.exe + ' exit=' + $lastExit)
    Add-Line '```text'
    Add-Line $lastOutput
    Add-Line '```'
    if ($lastExit -eq 0 -and (Test-Path $OutputPath)) { $ok = $true; break }
  }
  return @{ ok=$ok; exit=$lastExit; output=$lastOutput }
}

Add-Line '## Detached run'
$r1 = Invoke-PythonEngine $InputDetached $OutDetached
Add-Line '## Industrial run'
$r2 = Invoke-PythonEngine $InputIndustrial $OutIndustrial

if (-not $r1.ok -or -not $r2.ok) {
  Add-Line '## Status'
  Add-Line 'FAILED - one or more Python runs failed.'
  Write-Status ([ordered]@{ task_id=$TaskId; status='failed'; detached_ok=$r1.ok; industrial_ok=$r2.ok; run_dir=$RunDir; generated_at=(Get-Date -Format s) })
  Write-Output 'FAILED robust smoke test'
  exit 3
}

$DetachedJson = Get-Content -Raw -Encoding UTF8 $OutDetached | ConvertFrom-Json
$IndustrialJson = Get-Content -Raw -Encoding UTF8 $OutIndustrial | ConvertFrom-Json

Add-Line '## Detached London 250m2 totals'
Add-Line ('Min total GBP: ' + $DetachedJson.totals.min_total_gbp)
Add-Line ('Max total GBP: ' + $DetachedJson.totals.max_total_gbp)
Add-Line ('Mid total GBP: ' + $DetachedJson.totals.mid_total_gbp)
Add-Line ('Initial payment GBP: ' + $DetachedJson.totals.initial_payment_gbp)
Add-Line ('Recurring monthly GBP: ' + $DetachedJson.totals.recurring_payment_gbp_per_month)
Add-Line ('Line count: ' + $DetachedJson.lines.Count)
Add-Line ''
Add-Line '## Industrial food factory 2500m2 totals'
Add-Line ('Min total GBP: ' + $IndustrialJson.totals.min_total_gbp)
Add-Line ('Max total GBP: ' + $IndustrialJson.totals.max_total_gbp)
Add-Line ('Mid total GBP: ' + $IndustrialJson.totals.mid_total_gbp)
Add-Line ('Initial payment GBP: ' + $IndustrialJson.totals.initial_payment_gbp)
Add-Line ('Recurring monthly GBP: ' + $IndustrialJson.totals.recurring_payment_gbp_per_month)
Add-Line ('Line count: ' + $IndustrialJson.lines.Count)
Add-Line ''
Add-Line '## Status'
Add-Line 'OK - robust smoke test completed.'

Write-Status ([ordered]@{
  task_id=$TaskId
  status='completed'
  run_dir=$RunDir
  detached=$DetachedJson.totals
  industrial=$IndustrialJson.totals
  generated_at=(Get-Date -Format s)
})

Write-Output 'OK TerraYield cost engine robust smoke test completed'
Write-Output ('RunDir=' + $RunDir)
Write-Output ('DetachedMidTotal=' + $DetachedJson.totals.mid_total_gbp)
Write-Output ('IndustrialMidTotal=' + $IndustrialJson.totals.mid_total_gbp)
exit 0
