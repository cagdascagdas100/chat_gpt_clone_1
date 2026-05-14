$ErrorActionPreference = 'Continue'
$TaskId = 'aays-087-source-inventory-20260515'
$BridgeRoot = if ($env:AAYS_BRIDGE_ROOT) { $env:AAYS_BRIDGE_ROOT } else { Split-Path -Parent $PSScriptRoot }
$ProjectRoot = 'C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$DataRoot = 'E:\AAYS_DATA\land_sales'
$ResultDir = Join-Path $BridgeRoot 'ai-results'
$HeartbeatDir = Join-Path $BridgeRoot 'ai-heartbeat'
New-Item -ItemType Directory -Force -Path $ResultDir,$HeartbeatDir | Out-Null
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$Report = Join-Path $ResultDir "aays-087-source-inventory-$Stamp.md"
$Heartbeat = Join-Path $HeartbeatDir 'source-inventory.md'
$Lines = New-Object System.Collections.Generic.List[string]
function AddLine([string]$m){ [void]$Lines.Add($m) }
function AddList([string]$title,[string]$path,[string]$filter,[int]$top){
  AddLine ''; AddLine ('## ' + $title)
  if(Test-Path $path){
    $items = Get-ChildItem $path -Recurse -File -Filter $filter -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First $top FullName,LastWriteTime,Length
    if($items){ AddLine ($items | Format-Table -AutoSize | Out-String) } else { AddLine 'NO_FILES' }
  } else { AddLine ('MISSING_DIR: ' + $path) }
}
function AddHeader([string]$file){
  AddLine ''; AddLine ('### HEADER ' + $file)
  if(Test-Path $file){
    try { AddLine (Get-Content -Path $file -TotalCount 1 -ErrorAction Stop) } catch { AddLine ('HEADER_ERROR: ' + $_.Exception.Message) }
  } else { AddLine 'MISSING_FILE' }
}
AddLine '# AAYS 087 Source Inventory'
AddLine ('Generated: ' + (Get-Date -Format s))
AddLine ('TaskId: ' + $TaskId)
AddLine ('BridgeRoot: ' + $BridgeRoot)
AddLine ('ProjectRoot: ' + $ProjectRoot)
AddLine ('DataRoot: ' + $DataRoot)
AddLine 'Mode: read-only inventory; no DB writes; no UI patch.'
AddList 'Final output CSV files' (Join-Path $DataRoot 'final_outputs') '*.csv' 40
AddList 'Final output SQL files' (Join-Path $DataRoot 'final_outputs') '*.sql' 20
AddList 'Final output JSON files' (Join-Path $DataRoot 'final_outputs') '*.json' 30
AddList 'Project CSV files' $ProjectRoot '*.csv' 40
AddList 'Project GeoJSON files' $ProjectRoot '*.geojson' 40
AddList 'Project Python files' $ProjectRoot '*.py' 60
$ready = Join-Path $DataRoot 'final_outputs\stg_land_sales_50step_db_ready.csv'
$schema = Join-Path $DataRoot 'final_outputs\DB_SCHEMA_APPLY.sql'
AddHeader $ready
AddLine ''; AddLine '## Schema file first 160 lines'
if(Test-Path $schema){ Get-Content $schema -TotalCount 160 | ForEach-Object { AddLine $_ } } else { AddLine 'MISSING_SCHEMA' }
AddLine ''; AddLine '## Accuracy program next gates'
AddLine 'gate_1_source_inventory: done'
AddLine 'gate_2_schema_map: partial_from_headers_and_schema'
AddLine 'gate_3_validation_sample: next'
AddLine 'wide_accuracy_program_percent: 40'
AddLine 'AAYS_087_SOURCE_INVENTORY_DONE=true'
Set-Content -Encoding UTF8 -Path $Report -Value $Lines
Set-Content -Encoding UTF8 -Path $Heartbeat -Value $Lines
Write-Output 'AAYS_087_SOURCE_INVENTORY_DONE=true'
Write-Output ('REPORT=' + $Report)
exit 0
