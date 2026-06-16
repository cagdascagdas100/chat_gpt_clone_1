# AAYS1 Future Growth smoke task
# Existing shared runner only. No new runner is started. No dummy or fake data is generated.
$ErrorActionPreference = 'Continue'
$pageKey = 'aays1'
$repoRoot = 'C:\Users\cagda\Documents\GitHub\AAYS'
$statusRoot = Join-Path $repoRoot 'docs\chatgpt_status\aays1'
$reportDir = Join-Path $statusRoot 'reports'
$statusDir = Join-Path $statusRoot 'status'
$heartbeatDir = Join-Path $statusRoot 'heartbeat'
New-Item -ItemType Directory -Force -Path $reportDir,$statusDir,$heartbeatDir | Out-Null
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$report = Join-Path $reportDir ('future_growth_local_admin_smoke_' + $stamp + '.txt')
function Add-Line([string]$s) { $s | Add-Content -LiteralPath $report -Encoding UTF8; Write-Host $s }
function HasText([string]$path,[string]$pattern) { if (Test-Path -LiteralPath $path) { return [bool](Select-String -Path $path -Pattern $pattern -Quiet -ErrorAction SilentlyContinue) } return $false }
Add-Line 'page_key=aays1'
Add-Line 'task=future-growth-100-db-layer-ui-smoke'
Add-Line 'status=local_runtime_gate_probe_required'
Add-Line 'no_new_runner_started=true'
Add-Line 'dummy_data_generated=false'
Add-Line "started_at=$(Get-Date -Format o)"
Add-Line "repo_root=$repoRoot"
$appJs = Join-Path $repoRoot 'england_map_web\app.js'
$routeFile = Join-Path $repoRoot 'terrayield_land_intelligence\app\api\routes\future_growth.py'
$tileFile = Join-Path $repoRoot 'terrayield_land_intelligence\app\future_growth\tile_service.py'
$evidenceFile = Join-Path $repoRoot 'terrayield_land_intelligence\app\future_growth\evidence_service.py'
$schemaFile = Join-Path $repoRoot 'terrayield_land_intelligence\app\schemas\future_growth.py'
$migrationFile = Join-Path $repoRoot 'terrayield_land_intelligence\alembic\versions\0007_future_growth_layer.py'
Add-Line ('future_icon_binding_present=' + (HasText $appJs 'future_growing_prognose.png'))
Add-Line ('future_layer_endpoint_marker_present=' + (HasText $appJs '/api/future-growth/layer'))
Add-Line ('backend_future_growth_route_file_present=' + (Test-Path -LiteralPath $routeFile))
Add-Line ('tile_service_file_present=' + (Test-Path -LiteralPath $tileFile))
Add-Line ('evidence_service_file_present=' + (Test-Path -LiteralPath $evidenceFile))
Add-Line ('schema_file_present=' + (Test-Path -LiteralPath $schemaFile))
Add-Line ('migration_0007_present=' + (Test-Path -LiteralPath $migrationFile))
Add-Line 'db_port_55460=not_verified_by_this_safe_wrapper'
Add-Line 'docker_api_ok=not_verified_by_this_safe_wrapper'
Add-Line 'layer_endpoint_ok=not_verified_by_this_safe_wrapper'
Add-Line 'colored_parcels_ok=not_verified_by_this_safe_wrapper'
Add-Line 'popup_required_fields_ok=not_verified_by_this_safe_wrapper'
Add-Line 'completion=82'
Add-Line 'final_ready=false'
Add-Line 'product_final_ready=false'
Add-Line 'production_complete=false'
Add-Line 'data_gate=LOCAL_RUNTIME_SMOKE_REQUIRED'
Add-Line 'next_step=existing_shared_runner_or_local_handoff_runbook_must_perform_real_postgis_layer_and_popup_smoke'
Add-Line "finished_at=$(Get-Date -Format o)"
"page_key=aays1`ntask=future-growth-100-db-layer-ui-smoke`ncompletion=82`nfinal_ready=false`nproduct_final_ready=false`nproduction_complete=false`ndata_gate=LOCAL_RUNTIME_SMOKE_REQUIRED`nreport=$report`nupdated_at=$(Get-Date -Format o)" | Set-Content -LiteralPath (Join-Path $statusDir 'future_growth_100_status_latest.txt') -Encoding UTF8
"page_key=aays1`ntask=future-growth-100-db-layer-ui-smoke`nstatus=script_executed`ncompletion=82`nupdated_at=$(Get-Date -Format o)" | Set-Content -LiteralPath (Join-Path $heartbeatDir 'future_growth_100_heartbeat.txt') -Encoding UTF8
exit 2
