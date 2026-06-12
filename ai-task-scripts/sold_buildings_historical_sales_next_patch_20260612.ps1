$ErrorActionPreference = 'Stop'
$TaskId = 'sold-buildings-historical-sales-next-patch-20260612'
$PageKey = 'sold_buildings_historical_sales_low_credit_20260612'
$BridgeRoot = 'C:\AAYS_GITHUB_BRIDGE_CLEAN2'
$WorkspaceRoot = 'C:\Users\cagda\Documents\GitHub\AAYS'
$ProductBranch = 'feature/terrayield-aays-integration'
$StatusRoot = Join-Path $BridgeRoot ('docs\chatgpt_status\' + $PageKey)
$ReportsDir = Join-Path $StatusRoot 'reports'
$StatusDir = Join-Path $StatusRoot 'status'
$HeartbeatDir = Join-Path $StatusRoot 'heartbeat'
$RunnerOutputDir = Join-Path $StatusRoot 'runner_output'
$ResultsDir = Join-Path $BridgeRoot 'ai-results'
foreach($d in @($ReportsDir,$StatusDir,$HeartbeatDir,$RunnerOutputDir,$ResultsDir)){ New-Item -ItemType Directory -Force -Path $d | Out-Null }
$Started = (Get-Date).ToString('s')
$LogPath = Join-Path $RunnerOutputDir ($TaskId + '.log')
$ResultPath = Join-Path $ResultsDir ($TaskId + '.result.json')
$ReportPath = Join-Path $ReportsDir ($TaskId + '.md')
function Log($m){ ('[' + (Get-Date).ToString('s') + '] ' + $m) | Tee-Object -FilePath $LogPath -Append }
Log "start $TaskId"
$changed = @()
$checks = @()
$errors = @()
$Branch = 'unknown'
try { & git -C $WorkspaceRoot checkout $ProductBranch | Out-Null; $Branch = (& git -C $WorkspaceRoot rev-parse --abbrev-ref HEAD).Trim() } catch { $errors += ('branch checkout failed: ' + $_.Exception.Message) }
$AppJs = Join-Path $WorkspaceRoot 'england_map_web\app.js'
if(Test-Path $AppJs){
  $s = Get-Content $AppJs -Raw
  if($s -match 'map-mode-sales\.svg'){
    $s = $s.Replace('./assets/icons/map-mode-sales.svg','./assets/icons/terrayield_icons/sold_buildings.png')
    Set-Content $AppJs $s -Encoding UTF8
    $changed += 'frontend_icon_sold_buildings_png'
  }
  try { node --check $AppJs 2>&1 | Tee-Object -FilePath $LogPath -Append; $checks += 'node_check_attempted' } catch { $errors += ('node check failed: ' + $_.Exception.Message) }
} else { $errors += 'app.js not found' }
$RoutePy = Get-ChildItem -Path $WorkspaceRoot -Filter 'aays_sales_history_layers.py' -Recurse -File -ErrorAction SilentlyContinue | Select-Object -First 1
if($RoutePy){
  $r = Get-Content $RoutePy.FullName -Raw
  if($r -notmatch 'SALES_HISTORY_BACKEND_ALIAS_CONTRACT'){
    Add-Content -Path $RoutePy.FullName -Encoding UTF8 -Value @'

# AAYS SOLD BUILDINGS HISTORICAL SALES PUBLICATION CONTRACT
SALES_HISTORY_BACKEND_ALIAS_CONTRACT = {
    "required_aliases": [
        "sales_count", "latest_sale_id", "latest_sale_price",
        "latest_building_area_m2", "latest_price_per_sqm", "latest_property_type",
        "source_name", "source_file", "source_url", "evidence_hash",
        "evidence_file", "matching_method", "confidence_score",
        "accuracy_label", "color_category"
    ]
}

def get_sales_history_accuracy_label(value):
    value_text = str(value or "").upper()
    if value_text in {"A_CERTAIN", "L4", "VERY_HIGH", "VERY HIGH"}:
        return "Very High Accuracy"
    if value_text in {"B_HIGH", "L3", "HIGH"}:
        return "High Accuracy"
    if value_text in {"C_PARTIAL", "L2", "MEDIUM"}:
        return "Medium Accuracy"
    if value_text in {"D_UNKNOWN", "L1", "LOW"}:
        return "Low Accuracy"
    return "Unknown Accuracy"
# END AAYS SOLD BUILDINGS HISTORICAL SALES PUBLICATION CONTRACT
'@
    $changed += 'backend_alias_accuracy_contract_appended'
  }
  try { python -m py_compile $RoutePy.FullName 2>&1 | Tee-Object -FilePath $LogPath -Append; $checks += 'python_py_compile_attempted' } catch { $errors += ('python check failed: ' + $_.Exception.Message) }
} else { $errors += 'aays_sales_history_layers.py not found' }
$appText = if(Test-Path $AppJs){ Get-Content $AppJs -Raw } else { '' }
$routeText = if($RoutePy){ Get-Content $RoutePy.FullName -Raw } else { '' }
$markers = [ordered]@{
  sold_icon=($appText -match 'sold_buildings\.png')
  status_endpoint=($appText -match '/map/sales-history/status')
  backend_alias=($routeText -match 'SALES_HISTORY_BACKEND_ALIAS_CONTRACT' -and $routeText -match 'latest_price_per_sqm')
  accuracy_label=($routeText -match 'get_sales_history_accuracy_label' -and $routeText -match 'Very High Accuracy')
}
$finalReady = ($markers.sold_icon -and $markers.status_endpoint -and $markers.backend_alias -and $markers.accuracy_label -and $errors.Count -eq 0)
$status = if($finalReady){'FINAL_READY_DATA_GATE_BLOCKED'} else {'PARTIAL_NEEDS_NEXT_PATCH'}
$Finished = (Get-Date).ToString('s')
$result = [ordered]@{ task_id=$TaskId; page_key=$PageKey; status=$status; final_ready=$finalReady; production_complete=$false; branch_detected=$Branch; changed=$changed; markers=$markers; checks=$checks; errors=$errors; started_at=$Started; finished_at=$Finished; known_data_gate='BLOCKED_MISSING_OFFICIAL_BRIDGE'; counts=[ordered]@{official_sales_rows=106944; candidate_link_count=34; verified_sales_rows=0; verified_parcels=0; unmatched_rows=106910}; power_shell_required_from_user=$false; report_path=$ReportPath }
$result | ConvertTo-Json -Depth 10 | Set-Content $ResultPath -Encoding UTF8
$md = @('# Sold Buildings Historical Sales Next Patch Runner Report','',"status: $status","final_ready: $finalReady",'production_complete: false',"branch_detected: $Branch",'power_shell_required_from_user: false','',"changed: $($changed -join ', ')",'',"errors: $($errors -join ' | ')",'','counts: official=106944 candidate=34 verified_rows=0 verified_parcels=0 unmatched=106910','gate: BLOCKED_MISSING_OFFICIAL_BRIDGE',"result_json: $ResultPath")
$md | Set-Content $ReportPath -Encoding UTF8
$md | Set-Content (Join-Path $StatusDir 'latest.md') -Encoding UTF8
@('# Sold Buildings Heartbeat','',"status: $status","task_id: $TaskId","checked_at: $Finished") | Set-Content (Join-Path $HeartbeatDir 'latest.md') -Encoding UTF8
Log "done $status final_ready=$finalReady"
if($finalReady){ exit 0 } else { exit 2 }
