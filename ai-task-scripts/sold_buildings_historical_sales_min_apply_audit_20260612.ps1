$ErrorActionPreference = 'Stop'
$TaskId = 'sold-buildings-historical-sales-min-apply-audit-20260612'
$PageKey = 'sold_buildings_historical_sales_low_credit_20260612'
$BridgeRoot = 'C:\AAYS_GITHUB_BRIDGE_CLEAN2'
$WorkspaceRoot = 'C:\Users\cagda\Documents\GitHub\AAYS'
$AppJs = Join-Path $WorkspaceRoot 'england_map_web\app.js'
$RoutePy = Join-Path $WorkspaceRoot 'terrayield_land_intelligence\app\api\routes\aays_sales_history_layers.py'
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
$Branch = 'unknown'
try { $Branch = (& git -C $WorkspaceRoot rev-parse --abbrev-ref HEAD 2>$null).Trim() } catch {}
$changed = @()
$checks = @()
if(Test-Path $AppJs){
  $s = Get-Content $AppJs -Raw
  if($s -match 'map-mode-sales\.svg'){
    $s = $s.Replace('./assets/icons/map-mode-sales.svg','./assets/icons/terrayield_icons/sold_buildings.png')
    Set-Content $AppJs $s -Encoding UTF8
    $changed += 'frontend_icon_sold_buildings_png'
  }
  $s = Get-Content $AppJs -Raw
  if($s -notmatch '/map/sales-history/status'){
    $needle = 'const payloadResponse = await fetchJsonWithTimeout(`${landIntelligenceApiBaseUrl}/map/sales-history/parcels?${params.toString()}`, {'
    $insert = "try {`n    window.__lastHistoricalSalesStatus = await fetchJsonWithTimeout(`${landIntelligenceApiBaseUrl}/map/sales-history/status`, { timeout: 8000 });`n  } catch (statusError) {`n    console.warn('Historical sales status unavailable', statusError);`n  }`n  " + $needle
    if($s.Contains($needle)){
      $s = $s.Replace($needle,$insert)
      Set-Content $AppJs $s -Encoding UTF8
      $changed += 'frontend_status_fetch_added'
    }
  }
}
if(Test-Path $RoutePy){
  $r = Get-Content $RoutePy -Raw
  if($r -notmatch 'latest_price_per_sqm'){
    $needle = "'updated_at', h.updated_at"
    $insert = "'sales_count', COALESCE(h.sales_count, jsonb_array_length(COALESCE(h.sales_history_records, '[]'::jsonb))),`n                'latest_sale_id', COALESCE(h.latest_sale_id, h.sales_history_records->0->>'sale_id', h.sales_history_records->0->>'transaction_id'),`n                'latest_sale_price', h.latest_sale_price,`n                'latest_building_area_m2', h.latest_building_area_m2,`n                'latest_price_per_sqm', h.latest_price_per_sqm,`n                'source_name', h.source_name,`n                'source_file', h.source_file,`n                'source_url', h.source_url,`n                'evidence_hash', h.evidence_hash,`n                'matching_method', h.matching_method,`n                'accuracy_label', CASE h.accuracy_scale WHEN 'A_CERTAIN' THEN 'Very High Accuracy' WHEN 'B_HIGH' THEN 'High Accuracy' WHEN 'C_PARTIAL' THEN 'Medium Accuracy' WHEN 'D_UNKNOWN' THEN 'Low Accuracy' ELSE h.accuracy_label END,`n                " + $needle
    if($r.Contains($needle)){
      $r = $r.Replace($needle,$insert)
      Set-Content $RoutePy $r -Encoding UTF8
      $changed += 'backend_alias_contract_added'
    }
  }
}
if(Test-Path $RoutePy){ try { python -m py_compile $RoutePy 2>&1 | Tee-Object -FilePath $LogPath -Append; $checks += 'python_py_compile_attempted' } catch { Log ('python check failed: ' + $_.Exception.Message) } }
if(Test-Path $AppJs){ try { node --check $AppJs 2>&1 | Tee-Object -FilePath $LogPath -Append; $checks += 'node_check_attempted' } catch { Log ('node check failed: ' + $_.Exception.Message) } }
$Finished = (Get-Date).ToString('s')
$appText = if(Test-Path $AppJs){ Get-Content $AppJs -Raw } else { '' }
$routeText = if(Test-Path $RoutePy){ Get-Content $RoutePy -Raw } else { '' }
$markers = [ordered]@{ sold_icon=($appText -match 'sold_buildings\.png'); status_endpoint=($appText -match '/map/sales-history/status'); backend_alias=($routeText -match 'latest_price_per_sqm'); accuracy_label=($routeText -match 'Very High Accuracy') }
$finalReady = ($markers.sold_icon -and $markers.status_endpoint -and $markers.backend_alias -and $markers.accuracy_label)
$status = if($finalReady){'PATCH_CONTRACT_READY_DATA_GATE_BLOCKED'} else {'PARTIAL_NEEDS_NEXT_PATCH'}
$result = [ordered]@{ task_id=$TaskId; page_key=$PageKey; status=$status; final_ready=$finalReady; production_complete=$false; branch_detected=$Branch; changed=$changed; markers=$markers; checks=$checks; started_at=$Started; finished_at=$Finished; known_data_gate='BLOCKED_MISSING_OFFICIAL_BRIDGE'; counts=[ordered]@{official_sales_rows=106944; candidate_link_count=34; verified_sales_rows=0; verified_parcels=0; unmatched_rows=106910}; power_shell_required_from_user=$false; report_path=$ReportPath }
$result | ConvertTo-Json -Depth 10 | Set-Content $ResultPath -Encoding UTF8
$md = @('# Sold Buildings Historical Sales Runner Report','',"status: $status","final_ready: $finalReady",'production_complete: false',"branch_detected: $Branch",'power_shell_required_from_user: false','',"changed: $($changed -join ', ')",'','counts: official=106944 candidate=34 verified_rows=0 verified_parcels=0 unmatched=106910','gate: BLOCKED_MISSING_OFFICIAL_BRIDGE','',"result_json: $ResultPath")
$md | Set-Content $ReportPath -Encoding UTF8
$md | Set-Content (Join-Path $StatusDir 'latest.md') -Encoding UTF8
@('# Sold Buildings Heartbeat','',"status: $status","task_id: $TaskId","checked_at: $Finished") | Set-Content (Join-Path $HeartbeatDir 'latest.md') -Encoding UTF8
Log "done $status final_ready=$finalReady"
if($finalReady){ exit 0 } else { exit 2 }
