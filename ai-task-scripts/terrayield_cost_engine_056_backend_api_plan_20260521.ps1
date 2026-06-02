$ErrorActionPreference='Continue'
$TaskId='terrayield-cost-engine-056-backend-api-plan-20260521'
$Root=if($env:AAYS_BRIDGE_ROOT){$env:AAYS_BRIDGE_ROOT}else{Split-Path -Parent $PSScriptRoot}
$OutDir=Join-Path $Root 'ai-results/terrayield_cost_engine/step_056_backend_api_plan'
$HbDir=Join-Path $Root 'ai-heartbeat'
New-Item -ItemType Directory -Force -Path $OutDir,$HbDir|Out-Null
$Summary=Join-Path $OutDir 'summary.md'
$Status=Join-Path $OutDir 'status.json'
$Schema=Join-Path $OutDir 'cost_engine_api_schema.json'
$Plan=Join-Path $OutDir 'backend_integration_plan.md'
$Hb=Join-Path $HbDir 'portable-runner.md'
@('# runner','Status: running','TaskId: '+$TaskId,'Message: backend api plan started')|Set-Content -Encoding UTF8 $Hb
$EnginePath=Join-Path $Root 'terrayield_cost_engine/python_demo/terrayield_cost_engine_demo.py'
$engineExists=Test-Path $EnginePath
$schemaObj=[ordered]@{
  task_id=$TaskId
  db_write=$false
  production_deploy=$false
  endpoints=@(
    @{method='POST';path='/admin/cost/estimate';purpose='Create itemized estimate from building type, subtype, GIA, floors, spec and payment inputs'},
    @{method='GET';path='/parcels/{parcel_id}/cost-latest';purpose='Return latest cost estimate for parcel'},
    @{method='GET';path='/parcels/{parcel_id}/cost-history';purpose='Return cost estimate history for parcel'},
    @{method='GET';path='/cost/sources/status';purpose='Return source registry and quality gates'},
    @{method='POST';path='/admin/cost/sources/sync';purpose='Dry-run source sync only until DB write is explicitly approved'}
  )
  request_fields=@('building_type','subtype','location','floors','gia_m2','spec','dwelling_units','retail_ratio','residential_ratio','upfront_pct','payment_months','include_land','land_cost','vat_treatment')
  response_fields=@('input','base_rate','lines','totals','validation','source_registry_subset')
  required_line_fields=@('main_category','sub_category','cost_item_name','unit','quantity','min_total_gbp','max_total_gbp','mid_total_gbp','initial_payment_gbp','recurring_payment_gbp_per_month','payment_type','source_id','source_url','evidence_text','confidence','correctness_score_4')
  quality_gates=@('No evidence_text no import','No source_url no HIGH confidence','Official or BCIS or quote required for 4/4','Seed fallback max 1-2/4','No production DB write by default')
}
$schemaObj|ConvertTo-Json -Depth 12|Set-Content -Encoding UTF8 $Schema
@('# TerraYield Cost Engine 056 Backend/API Integration Plan','','## Status','Prepared backend/API integration plan artifacts.','','## Engine file','- Path: '+$EnginePath,'- Exists: '+$engineExists,'','## Next implementation steps','1. Add FastAPI adapter around terrayield_cost_engine_demo.py.','2. Add request/response Pydantic schemas matching cost_engine_api_schema.json.','3. Add dry-run endpoint tests for detached, apartment, retail, mixed-use and industrial cases.','4. Add DB model draft only; do not apply migration.','5. Add source quality validation before any estimate is accepted.','','## Safety','- DB write: false','- Production deploy: false','- Migration apply: false','- Secrets: not read or printed','','TASK_COMPLETION=100/100')|Set-Content -Encoding UTF8 $Plan
@('# TerraYield Cost Engine 056 Backend/API Plan','',('Status: completed'),('Engine exists: '+$engineExists),'Output files:','- '+$Schema,'- '+$Plan,'','No DB write. No migration. No production deploy.','TASK_COMPLETION=100/100')|Set-Content -Encoding UTF8 $Summary
[ordered]@{task_id=$TaskId;status='completed';engine_exists=$engineExists;schema=$Schema;plan=$Plan;summary=$Summary;db_write=$false;production_deploy=$false;no_migration=$true;next_task='terrayield-cost-engine-057-fastapi-adapter-dry-run'}|ConvertTo-Json -Depth 8|Set-Content -Encoding UTF8 $Status
@('# runner','Status: finished','TaskId: '+$TaskId,'Message: exit=0')|Set-Content -Encoding UTF8 $Hb
Write-Output 'OK TerraYield cost engine backend/API plan completed'
exit 0
