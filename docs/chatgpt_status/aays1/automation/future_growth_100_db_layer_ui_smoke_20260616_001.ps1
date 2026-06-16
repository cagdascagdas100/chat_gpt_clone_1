# AAYS1 Future Growth smoke task
# Existing shared runner only. This script does not start another runner and does not generate dummy data.
$pageKey = 'aays1'
$repoRoot = 'C:\Users\cagda\Documents\GitHub\AAYS'
$reportDir = Join-Path $repoRoot 'docs\chatgpt_status\aays1\reports'
$statusDir = Join-Path $repoRoot 'docs\chatgpt_status\aays1\status'
New-Item -ItemType Directory -Force -Path $reportDir | Out-Null
New-Item -ItemType Directory -Force -Path $statusDir | Out-Null
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$report = Join-Path $reportDir ('future_growth_local_admin_smoke_' + $stamp + '.txt')
function Add-Line([string]$s) { $s | Add-Content -LiteralPath $report -Encoding UTF8; Write-Host $s }
function HasText([string]$path,[string]$pattern) { if (Test-Path -LiteralPath $path) { return [bool](Select-String -Path $path -Pattern $pattern -Quiet -ErrorAction SilentlyContinue) } return $false }
Add-Line 'page_key=aays1'
Add-Line 'task=future-growth-100-db-layer-ui-smoke'
Add-Line 'status=preflight_report_only'
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
Add-Line 'completion=76'
Add-Line 'final_ready=false'
Add-Line 'product_final_ready=false'
Add-Line 'production_complete=false'
Add-Line 'data_gate=LOCAL_RUNTIME_SMOKE_REQUIRED'
Add-Line 'next_step=existing_shared_runner_must_execute_local_docker_postgis_and_api_smoke_from_handoff_package'
Add-Line "finished_at=$(Get-Date -Format o)"
"page_key=aays1`ntask=future-growth-100-db-layer-ui-smoke`ncompletion=76`nfinal_ready=false`ndata_gate=LOCAL_RUNTIME_SMOKE_REQUIRED`nreport=$report" | Set-Content -LiteralPath (Join-Path $statusDir ('future_growth_100_status_' + $stamp + '.txt')) -Encoding UTF8
exit 2
