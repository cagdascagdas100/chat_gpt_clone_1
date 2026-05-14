# TY135 App Route Integration Inventory

## Existing integration locations
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\main.py
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\schemas

## Export files
- E:\AAYS_DATA\contractor\exports\contractors_for_app.csv exists bytes=63729 modified=2026-05-14T13:21:38
- E:\AAYS_DATA\contractor\exports\contractors_for_app.jsonl exists bytes=280330 modified=2026-05-14T13:21:42
- E:\AAYS_DATA\contractor\exports\contractor_projects_for_app.csv exists bytes=405940 modified=2026-05-14T13:21:42
- E:\AAYS_DATA\contractor\exports\contractor_parcel_matches_for_app.csv exists bytes=5688 modified=2026-05-14T13:21:42
- E:\AAYS_DATA\contractor\exports\export_manifest.json exists bytes=867 modified=2026-05-14T13:21:42

## Route/service hits
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\main.py:7: from fastapi import FastAPI
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\main.py:11: from app.api.routes import admin, brownfield, contractor, cost, etl, facilities, future_growth, health, listings, map_layers, ops, parcels, planned_assets, proxy, sources
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\main.py:17: app = FastAPI(
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\main.py:31: app.include_router(health.router)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\main.py:32: app.include_router(sources.router)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\main.py:33: app.include_router(admin.router)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\main.py:34: app.include_router(etl.router)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\main.py:35: app.include_router(facilities.router)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\main.py:36: app.include_router(cost.router)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\main.py:37: app.include_router(cost.admin_router)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\main.py:38: app.include_router(parcels.router)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\main.py:39: app.include_router(planned_assets.router)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\aays_sales_history_layers.py:7: from fastapi import APIRouter, HTTPException
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\aays_sales_history_layers.py:16: router = APIRouter(tags=["aays-sales-history"])
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\aays_sales_history_layers.py:85: @router.get("/map/sales-history/status")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\aays_sales_history_layers.py:115: avg_reliability = row.get("avg_reliability_score")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\aays_sales_history_layers.py:119: "verified_parcel_count": int(row.get("verified_parcel_count") or 0),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\aays_sales_history_layers.py:120: "last_ingest_at": row.get("last_ingest_at"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\aays_sales_history_layers.py:125: @router.get("/map/sales-history/external-evidence")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\aays_sales_history_layers.py:215: @router.get("/map/sales-history/parcels")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\aays_sales_history_layers.py:346: @router.get("/map/sales-history/combined")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\aays_sales_history_layers.py:459: @router.get("/map/sales-history/l4-reviewed-package/status")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\aays_sales_history_layers.py:462: counts = data.get("counts", {})
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\aays_sales_history_layers.py:476: @router.get("/map/sales-history/l4-reviewed-package")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\aays_sales_layers.py:5: from fastapi import APIRouter
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\aays_sales_layers.py:10: router = APIRouter(tags=["aays-sales-layers"])
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\aays_sales_layers.py:33: @router.get("/map/sales-layers/external-market")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\aays_sales_layers.py:120: @router.get("/map/sales-layers/verified-history")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\aays_sale_land_verification.py:3: from fastapi import APIRouter
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\aays_sale_land_verification.py:7: router = APIRouter(prefix="/verification/sale-land", tags=["sale-land-verification"])
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\aays_sale_land_verification.py:10: @router.post("/classify")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\admin.py:3: from fastapi import APIRouter, Depends, HTTPException, Query
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\admin.py:32: router = APIRouter(prefix="/admin", tags=["admin"])
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\admin.py:35: @router.get("/coverage", response_model=BackendCoverageSummary)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\admin.py:40: @router.get("/seed-candidates", response_model=list[AdminSeedCandidate])
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\admin.py:62: @router.get("/supabase/status", response_model=SupabaseSyncStatus)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\admin.py:67: @router.get("/supabase/records", response_model=list[SupabaseLandListingRecord])
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\admin.py:87: @router.post("/supabase/records", response_model=SupabaseLandListingRecord)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\admin.py:99: @router.post("/supabase/records/bulk", response_model=SupabaseBulkUpsertResult)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\admin.py:111: @router.delete("/supabase/records/{record_id}", response_model=SupabaseDeleteResult)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\admin.py:123: @router.post("/supabase/sync", response_model=SupabaseSyncResult)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\admin.py:139: @router.get("/managed-sales/status", response_model=SupabaseSyncStatus)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\admin.py:144: @router.get("/managed-sales/records", response_model=list[SupabaseLandListingRecord])
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\brownfield.py:3: from fastapi import APIRouter, Query
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\brownfield.py:10: router = APIRouter(prefix='/brownfield-sites', tags=['brownfield'])
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\brownfield.py:20: @router.get('', response_model=None)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\brownfield.py:46: @router.get('/{site_id}', response_model=BrownfieldSiteDetail)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\contractor.py:8: from fastapi import APIRouter, HTTPException, Query
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\contractor.py:11: from app.schemas.contractor import (
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\contractor.py:12: ContractorExportRowsResponse,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\contractor.py:13: ContractorParcelContactsResponse,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\contractor.py:14: ContractorStatusResponse,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\contractor.py:16: from app.services.runtime_ops_service import get_runtime_storage_registry
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\contractor.py:18: router = APIRouter(prefix="/api/contractor", tags=["contractor"])
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\contractor.py:23: return (settings.contractor_export_root or (settings.contractor_storage_root / "exports")).resolve()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\contractor.py:28: return (settings.contractor_manifest_root or (settings.contractor_storage_root / "manifests")).resolve()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\contractor.py:60: value = payload.get(key)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\contractor.py:99: if parcel_id is not None and str(row.get("parcel_id") or "").strip() != parcel_id:
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\contractor.py:118: str(preflight.get("status", "")).lower() == "completed"
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\cost.py:3: from fastapi import APIRouter, Depends, HTTPException, Query
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\cost.py:38: router = APIRouter(tags=["cost"])
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\cost.py:39: admin_router = APIRouter(prefix="/admin/cost", tags=["cost-admin"])
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\cost.py:42: @admin_router.post("/sources/sync", response_model=CostSourceSyncResult)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\cost.py:54: @admin_router.post("/estimate", response_model=CostEstimateResponse)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\cost.py:66: @router.get("/parcels/{parcel_id}/cost-latest", response_model=CostEstimateResponse)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\cost.py:74: @router.get("/parcels/{parcel_id}/cost-history", response_model=list[ParcelCostEstimateHistoryItem])
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\cost.py:83: @router.get("/cost/sources/status", response_model=CostSourceStatusResponse)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\cost.py:91: @router.get("/cost/integration/status", response_model=Cost50IntegrationStatusResponse)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\cost.py:98: @router.get("/cost/integration/artifacts", response_model=Cost50ArtifactIndexResponse)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\cost.py:105: @router.get("/handoff/status", response_model=Cost50IntegrationStatusResponse)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\cost.py:112: @router.get("/handoff/evidence", response_model=Cost50ArtifactIndexResponse)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\etl.py:3: from fastapi import APIRouter, Query
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\etl.py:9: router = APIRouter(prefix='/etl', tags=['etl'])
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\etl.py:12: @router.post('/run', response_model=list[ETLRunResponse])
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\etl.py:17: @router.get('/runs', response_model=list[ETLRunResponse])
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\facilities.py:3: from fastapi import APIRouter, Query
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\facilities.py:10: router = APIRouter(prefix="/facilities", tags=["facilities"])
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\facilities.py:13: @router.get("", response_model=None)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\future_growth.py:5: from fastapi import APIRouter, HTTPException, Query, status
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\future_growth.py:27: router = APIRouter(prefix="/api/future-growth", tags=["future-growth"])
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\future_growth.py:37: @router.get("/layer", response_model=FutureGrowthLayerResponse)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\future_growth.py:59: @router.get("/parcels/{parcel_id}", response_model=FutureGrowthParcelDetailResponse)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\future_growth.py:66: @router.get("/parcels/{parcel_id}/evidence", response_model=list[FutureGrowthEvidenceItem])
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\future_growth.py:74: @router.get("/cities/{city_id}/vector", response_model=FutureGrowthVectorResponse)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\future_growth.py:81: @router.get("/local-authorities/{code}/vector", response_model=FutureGrowthVectorResponse)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\future_growth.py:88: @router.get("/methodology", response_model=FutureGrowthMethodologyResponse)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\future_growth.py:109: @router.post("/jobs", response_model=FutureGrowthJobResponse)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\health.py:3: from fastapi import APIRouter
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\health.py:10: router = APIRouter(tags=['health'])
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\health.py:13: @router.get('/health', response_model=HealthResponse)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\listings.py:3: from fastapi import APIRouter, Query
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\listings.py:12: router = APIRouter(prefix='/listings', tags=['listings'])
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\listings.py:22: @router.get('', response_model=None)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\listings.py:66: @router.get('/managed-sales', response_model=list[SupabaseLandListingRecord])
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\listings.py:75: @router.get('/{listing_id}', response_model=ListingDetail)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\map_layers.py:3: from fastapi import APIRouter, Query
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\map_layers.py:11: router = APIRouter(prefix='/map', tags=['map'])
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\map_layers.py:21: @router.get('/parcels', response_model=GeoJSONFeatureCollection)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\map_layers.py:68: @router.get('/listings', response_model=GeoJSONFeatureCollection)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\map_layers.py:104: @router.get('/brownfield', response_model=GeoJSONFeatureCollection)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\map_layers.py:128: @router.get("/map/sales-layers/external-market")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\map_layers.py:195: @router.get("/map/sales-layers/verified-history")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\ops.py:3: from fastapi import APIRouter, Query
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\ops.py:6: from app.schemas.ops import RuntimeConsistencyCheckResponse, RuntimeStorageRegistryResponse
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\ops.py:7: from app.services.runtime_ops_service import (
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\ops.py:13: router = APIRouter(prefix="/ops", tags=["ops"])
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\ops.py:16: @router.get("/storage-registry", response_model=RuntimeStorageRegistryResponse)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\ops.py:21: @router.get("/consistency-check", response_model=RuntimeConsistencyCheckResponse)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\parcels.py:3: from fastapi import APIRouter, Query
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\parcels.py:12: router = APIRouter(prefix='/parcels', tags=['parcels'])
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\parcels.py:22: @router.get('', response_model=None)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\parcels.py:82: @router.get('/{parcel_id}', response_model=ParcelDetail)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\parcels.py:87: @router.get('/{parcel_id}/signals', response_model=ParcelSignalItem)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\parcels.py:92: @router.get('/{parcel_id}/context', response_model=ParcelContextSummaryItem)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\parcels.py:97: @router.get('/{parcel_id}/scores', response_model=list[ParcelScenarioScoreItem])
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\parcels.py:102: @router.get('/{parcel_id}/history', response_model=list[ParcelHistoryItem])
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\planned_assets.py:3: from fastapi import APIRouter, Depends, Query
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\planned_assets.py:26: router = APIRouter(tags=["planned-assets"])
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\planned_assets.py:27: admin_router = APIRouter(prefix="/admin/planned-assets", tags=["planned-assets-admin"])
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\planned_assets.py:30: @router.get("/parcels/{parcel_id}/planned-assets", response_model=list[PlannedAssetItem])
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\planned_assets.py:39: @router.get("/parcels/{parcel_id}/future-growth-score", response_model=ParcelFutureGrowthScoreResponse)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\planned_assets.py:47: @router.get("/planned-assets/search", response_model=list[PlannedAssetItem])
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\planned_assets.py:70: @router.get("/planned-assets/nearby", response_model=list[PlannedAssetItem])
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\planned_assets.py:81: @router.get("/planned-assets/sources", response_model=list[PlannedAssetSourceItem])
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\planned_assets.py:86: @router.get("/planned-assets/{planned_asset_id}", response_model=PlannedAssetItem)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\planned_assets.py:91: @admin_router.post("/ingest", response_model=PlannedAssetsIngestResponse)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\planned_assets.py:100: @admin_router.post("/recalculate-scores", response_model=PlannedAssetsRecalculateResponse)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\proxy.py:6: from fastapi import APIRouter, HTTPException, Request
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\proxy.py:34: router = APIRouter(prefix="/proxy", tags=["proxy"])
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\proxy.py:51: direct_url = PARCEL_DIRECT_URLS.get(filename)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\proxy.py:61: value = request.headers.get(name)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\proxy.py:70: value = response.headers.get(name)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\proxy.py:76: @router.api_route("/parcels/{path:path}", methods=["GET", "HEAD"])
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\proxy.py:79: local_path = LOCAL_PARCEL_FILES.get(filename)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\proxy.py:119: media_type=headers.get("content-type"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\sources.py:3: from fastapi import APIRouter
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\sources.py:9: router = APIRouter(prefix='/sources', tags=['sources'])
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\sources.py:12: @router.get('', response_model=list[SourceDescriptor])
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\sources.py:17: @router.get('/status', response_model=list[SourceStatus])
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\clients\supabase_rest.py:63: response = client.get(self._table_url(), params=params)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\clients\supabase_rest.py:79: response = client.post(self._table_url(), params=params, json=rows)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\core\config.py:22: model_config = SettingsConfigDict(env_file='.env', env_prefix='TYLI_', extra='ignore')
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\core\config.py:158: contractor_storage_root: Path = Field(default_factory=lambda: Path(r'E:\AAYS_DATA\contractor'))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\core\config.py:159: contractor_export_root: Path | None = None
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\core\config.py:160: contractor_manifest_root: Path | None = None
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\core\config.py:161: contractor_preflight_audit_path: Path = Field(
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\core\config.py:162: default_factory=lambda: Path(r'C:\AAYS1_GITHUB_BRIDGE\chat_gpt_clone_1\ai-results\terrayield-079-contractor-db-env-loader-preflight.audit.json')
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\core\db_resolver.py:54: value = _read_env_like_file(path).get(key)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\core\ttl_cache.py:21: def get(self, key: str) -> Optional[Any]:
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\core\ttl_cache.py:24: entry = self._items.get(key)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\apply_repo_manual_match_overrides.py:11: r"C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\data\live_feeds\drops\market\repo_manual_match_batch_immediate.csv"
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\apply_repo_manual_match_overrides.py:14: r"C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\data\live_feeds\drops\market\repo_manual_match_immediate_overrides.json"
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\apply_repo_manual_match_overrides.py:57: listing_id = (row.get("listing_id") or "").strip()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\apply_repo_manual_match_overrides.py:58: override = overrides.get(listing_id)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\apply_repo_manual_match_overrides.py:72: row[field] = _stringify(override.get(field))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\apply_repo_manual_match_overrides.py:74: row["point_wkt"] = _stringify(override.get("point_wkt"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\apply_repo_manual_match_overrides.py:75: note_suffix = _stringify(override.get("location_notes_append"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\apply_repo_manual_match_overrides.py:77: row["location_notes"] = _append_note(row.get("location_notes") or "", note_suffix)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\authority_checkpoint.py:111: row_count = int(metadata.get("row_count") or 0)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\bootstrap_homes_england_handoff.py:46: status = str(state.get("status") or "")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\bootstrap_homes_england_handoff.py:47: current_authority = str(state.get("current_authority") or "").strip()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\bootstrap_homes_england_handoff.py:48: current_offset = state.get("current_offset")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\bootstrap_homes_england_handoff.py:49: completed_authorities = [str(item) for item in state.get("completed_authorities", [])]
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\bootstrap_homes_england_handoff.py:50: completed_offsets = [int(item) for item in state.get("completed_offsets", [])]
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\bootstrap_homes_england_handoff.py:75: "handoff_mode": handoff_manifest.get("handoff_mode"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\bootstrap_homes_england_handoff.py:118: status = item.get("status")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\build_authority_subset_manifest.py:15: r"C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\data\live_feeds\drops\market\repo_manual_match_batch_authority_expansion.csv"
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\build_authority_subset_manifest.py:27: local_authority = (row.get("local_authority") or "").strip()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\build_authority_subset_manifest.py:32: matched_inspire_id = (row.get("matched_inspire_id") or "").strip()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\build_authority_subset_manifest.py:42: records = payload.get("records") if isinstance(payload, dict) else payload
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\build_authority_subset_manifest.py:81: if str(row.get("authority") or "").strip() == authority_text:
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\build_authority_subset_manifest.py:84: candidate = str(row.get("authority") or "").strip()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\build_authority_subset_manifest.py:120: matched_authority = str(matched_row.get("authority") or "").strip()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\build_england_region_chunk_matrix.py:64: target_count = counts.get(chunk_index, 0)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\build_local_brownfield_manifest_candidates.py:72: reviewed = sum(1 for row in candidate_rows if row.get('requires_manual_review'))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\build_local_brownfield_manifest_candidates.py:73: evidenced = sum(1 for row in candidate_rows if row.get('planning_data_count'))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\build_local_brownfield_manifest_candidates.py:74: active = sum(1 for row in candidate_rows if row.get('is_active'))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\build_local_brownfield_manifest_candidates.py:106: 'candidate_root_urls': '; '.join(row.get('candidate_root_urls', [])),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\build_local_brownfield_manifest_candidates.py:107: 'sample_site_plan_urls': '; '.join(row.get('sample_site_plan_urls', [])),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\build_local_brownfield_manifest_candidates.py:108: 'sample_source_record_ids': '; '.join(row.get('sample_source_record_ids', [])),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\build_local_brownfield_manifest_candidates.py:109: 'organisation_entities': '; '.join(row.get('organisation_entities', [])),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\build_local_brownfield_manifest_candidates.py:110: 'discovery_match_methods': '; '.join(row.get('discovery_match_methods', [])),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\build_local_brownfield_manifest_candidates.py:111: 'raw_authority_values': '; '.join(row.get('raw_authority_values', [])),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\build_market_integration_package.py:136: source_origin = _clean(row.get("source_polygon_origin"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\build_market_integration_package.py:137: site_status = _clean(row.get("source_polygon_original_site_status"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\build_market_integration_package.py:138: parcel_origin = _clean(row.get("parcel_polygon_origin"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\build_market_integration_package.py:139: match_origin = _clean(row.get("match_origin"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\build_market_integration_package.py:140: record_state = _clean(row.get("record_state"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\build_market_integration_package.py:142: display_geojson_obj = _json_obj(_clean(row.get("listing_plan_polygon_geojson")))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\build_market_integration_package.py:143: parcel_geojson_obj = _json_obj(_clean(row.get("parcel_geom_geojson")))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\build_market_integration_package.py:192: "listing_id": _clean(row.get("listing_id")),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\build_market_integration_package.py:193: "provider_listing_id": _clean(row.get("provider_listing_id")),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\build_market_integration_package.py:194: "listing_status": _clean(row.get("listing_status")),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\build_market_integration_package.py:195: "ask_price": _clean(row.get("ask_price")),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\build_market_integration_package.py:196: "listing_url": _clean(row.get("listing_url")),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\build_market_polygon_provenance.py:16: r"C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\data\live_feeds\drops\market\repo_master_market_input_force_2026-04-23_sridfix.csv"
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\build_market_polygon_provenance.py:37: return bool(_clean(row.get("matched_parcel_ref")) or _clean(row.get("matched_inspire_id")))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\build_market_polygon_provenance.py:58: notes = _clean((source_row or {}).get("location_notes"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\build_market_polygon_provenance.py:67: method = _clean(row.get("match_method"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\build_market_polygon_provenance.py:74: if _clean(row.get("record_state")) == "matched":
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\build_market_polygon_provenance.py:76: notes = _clean((source_row or {}).get("location_notes"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\build_market_polygon_provenance.py:85: if _clean(row.get("record_state")) == "matched_provisional":
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\build_market_polygon_provenance.py:140: integrity_status = _clean(row.get("pipeline_polygon_integrity_status"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\build_market_polygon_provenance.py:141: risk_tier = _clean(row.get("risk_tier"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\build_market_polygon_provenance.py:172: source_by_id = {(row.get("listing_id") or "").strip(): row for row in source_rows if _clean(row.get("listing_id"))}
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\build_market_polygon_provenance.py:178: listing_id = _clean(row.get("listing_id"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\build_market_polygon_provenance.py:179: source_row = source_by_id.get(listing_id)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\england_all_sales_candidate_geometry_builder.py:144: if c.get("udt_name") == "geometry" or c["column_name"].lower() in ("geometry", "geom", "footprint", "polygon"):
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\england_all_sales_candidate_geometry_builder.py:147: json_cols = [c["column_name"] for c in cols if c.get("udt_name") in ("json", "jsonb") or "raw" in c["column_name"].lower() or "metadata" in c["column_name"].lower()]
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\england_all_sales_candidate_geometry_builder.py:148: text_cols = [c["column_name"] for c in cols if c.get("data_type") in ("text", "character varying")][:20]
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\england_all_sales_candidate_geometry_builder.py:230: if gj.get("type") == "Polygon":
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\england_all_sales_candidate_geometry_builder.py:232: if gj.get("type") == "MultiPolygon":
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\england_all_sales_candidate_geometry_builder.py:381: lid = clean(r.get("listing_id")) or clean(r.get("provider_listing_id")) or f"SRC-{i}"
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\england_all_sales_candidate_geometry_builder.py:382: if lid.isdigit() and "onthemarket" in clean(r.get("listing_url")).lower():
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\england_all_sales_candidate_geometry_builder.py:407: lon = safe_float(r.get("centroid_lon"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\england_all_sales_candidate_geometry_builder.py:408: lat = safe_float(r.get("centroid_lat"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\england_all_sales_candidate_geometry_builder.py:409: feed = parse_geojson(clean(r.get("feed_polygon_geojson")))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\england_all_sales_candidate_geometry_builder.py:420: evtext = clean(r.get("evidence_text"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\england_all_sales_candidate_geometry_builder.py:423: counts[conf] = counts.get(conf, 0) + 1
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\england_deep_sales_source_confidence_booster.py:38: r = requests.get(url, headers={"User-Agent":"Mozilla/5.0 sale-geometry-evidence/1.0","Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"}, timeout=25)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\england_deep_sales_source_confidence_booster.py:74: r = requests.get(url, headers={"User-Agent":"Mozilla/5.0 sale-geometry-evidence/1.0"}, timeout=35)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\england_deep_sales_source_confidence_booster.py:77: ctype = r.headers.get("content-type", "").lower()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\england_deep_sales_source_confidence_booster.py:92: downloaded_urls=[d["url"] for d in downloaded if d.get("path")]
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\england_deep_sales_source_confidence_booster.py:93: combined=" ".join([page_text or "", " ".join(downloaded_urls+[d.get("path","") for d in downloaded]), clean(row.get("verification_note")), clean(row.get("strict_verification_note")), clean(row.get("area_raw")), clean(row.get("generation_method"))])
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\england_deep_sales_source_confidence_booster.py:95: source_area=bool(area_hits) or clean(row.get("area_source")).lower() in {"source_text_area","public_site_area_text"}
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\england_deep_sales_source_confidence_booster.py:109: return {"deep_confidence_tier":tier,"deep_confidence_score":score,"deep_confidence_label":label,"source_area":"yes" if source_area else "no","plan_signal":"yes" if plan_signal else "no","public_doc_downloaded":"yes" if doc_signal else "no","reference_signal":"yes" if ref_signal else "no","polygon_signal":"yes" if polygon_signal else "no","area_hits":"; ".join(area_hits[:8]),"downloaded_count":len([d for d in downloaded if d.get("path")]),"downloaded_urls":" | ".join(downloaded_urls[:20])}
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\england_deep_sales_source_confidence_booster.py:121: lid=clean(row.get("listing_id")); url=clean(row.get("listing_url")); print(f"[{idx}/{len(rows)}] {lid} {url}",flush=True)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\england_deep_sales_source_confidence_booster.py:128: note=(f"DEEP_ENGLAND_SALES_SOURCE_CONFIDENCE | score={score['deep_confidence_score']} | tier={score['deep_confidence_tier']} | label={score['deep_confidence_label']} | source_area={score['source_area']} | plan_signal={score['plan_signal']} | public_doc={score['public_doc_downloaded']} | reference={score['reference_signal']} | polygon_signal={score['polygon_signal']} | area_hits={score['area_hits']} | area={clean(row.get('estimated_area_m2'))}m2 | perimeter={clean(row.get('perimeter_m'))}m | sides_m={clean(row.get('side_lengths_m_json'))} | sides_cm={clean(row.get('side_lengths_cm_json'))} | NOT official parcel match; non-A rows remain estimated sale geometry candidates.")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\england_deep_sales_source_confidence_booster.py:130: ranked.sort(key=lambda r:(-int(r.get("deep_confidence_score") or 0), clean(r.get("listing_id"))))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\england_deep_sales_source_confidence_booster.py:133: geom=clean(r.get("estimated_polygon_geojson"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\england_deep_sales_source_confidence_booster.py:134: if geom: apply_rows.append({"listing_id":clean(r.get("listing_id")),"verification_status":"derived","verified_polygon_geojson":geom,"verification_source_url":clean(r.get("listing_url")),"verification_note":clean(r.get("deep_verification_note"))[:4000]})
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\england_sales_source_discovery_and_geometry.py:134: est = estimates.get((schema, table), 0)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\england_sales_source_discovery_and_geometry.py:281: if gj.get("type") == "Polygon":
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\england_sales_source_discovery_and_geometry.py:283: if gj.get("type") == "MultiPolygon":
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\england_sales_source_discovery_and_geometry.py:408: lid = clean(r.get(lid_col)) if lid_col else ""
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\england_sales_source_discovery_and_geometry.py:409: provider = clean(r.get(provider_col)) if provider_col else ""
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\england_sales_source_discovery_and_geometry.py:410: url = clean(r.get(url_col)) if url_col else ""
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\england_sales_source_discovery_and_geometry.py:419: lon = safe_float(r.get(lon_col)) if lon_col else None
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\england_sales_source_discovery_and_geometry.py:420: lat = safe_float(r.get(lat_col)) if lat_col else None
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\england_sales_source_discovery_and_geometry.py:421: gj = parse_geojson(clean(r.get(gj_col))) if gj_col else None
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\england_sales_source_discovery_and_geometry.py:434: confidence_counts[conf] = confidence_counts.get(conf, 0) + 1
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\england_sales_source_discovery_and_geometry.py:456: "ask_price": clean(r.get(price_col)) if price_col else "",
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\england_sales_source_discovery_and_geometry.py:457: "postcode": clean(r.get(postcode_col)) if postcode_col else "",
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\enrich_public_listing_addresses.py:14: r"C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\data\live_feeds\drops\market\repo_manual_match_batch_immediate.csv"
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\enrich_public_listing_addresses.py:38: if _clean(row.get("matched_parcel_ref")) or _clean(row.get("matched_inspire_id")):
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\enrich_public_listing_addresses.py:40: return not _clean(row.get("latitude")) or not _clean(row.get("longitude"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\enrich_public_listing_addresses.py:99: address_text = _clean(row.get("address_text"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\enrich_public_listing_addresses.py:100: postcode = _clean(row.get("postcode"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\enrich_public_listing_addresses.py:101: local_authority = _clean(row.get("local_authority"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\enrich_public_listing_addresses.py:102: parcel_name = _clean(row.get("parcel_name"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\enrich_public_listing_addresses.py:103: title = _clean(row.get("title"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\enrich_public_listing_addresses.py:104: url_location = _listing_url_location_text(row.get("listing_url"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\enrich_public_listing_addresses.py:142: response = client.get(
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\enrich_public_listing_addresses.py:155: latitude = top.get("lat")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\enrich_public_listing_addresses.py:156: longitude = top.get("lon")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\enrich_public_listing_postcodes.py:11: r"C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\data\live_feeds\drops\market\manual_public_listing_expansion.csv"
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\enrich_public_listing_postcodes.py:24: postcode = _normalize_postcode(row.get("postcode"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\enrich_public_listing_postcodes.py:27: return not (row.get("latitude") or "").strip() or not (row.get("longitude") or "").strip()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\enrich_public_listing_postcodes.py:31: response = client.get(POSTCODES_API.format(postcode=postcode), timeout=20.0)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\enrich_public_listing_postcodes.py:36: result = payload.get("result") or {}
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\enrich_public_listing_postcodes.py:37: latitude = result.get("latitude")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\enrich_public_listing_postcodes.py:38: longitude = result.get("longitude")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\enrich_public_listing_postcodes.py:54: postcode = _normalize_postcode(row.get("postcode"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\estimated_candidate_geometry_builder.py:36: if gj.get('type')=='Polygon': return [[float(x),float(y)] for x,y in gj['coordinates'][0]]
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\estimated_candidate_geometry_builder.py:37: if gj.get('type')=='MultiPolygon': return [[float(x),float(y)] for x,y in gj['coordinates'][0][0]]
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\estimated_candidate_geometry_builder.py:68: for a in ev.get('areas') or []:
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\estimated_candidate_geometry_builder.py:70: m2=float(a.get('m2')); raw=clean(a.get('raw'))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\estimated_candidate_geometry_builder.py:88: if clean(r.get('final_polygon_decision')).lower()=='derived' and clean(r.get('confidence')).lower()=='medium':
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\estimated_candidate_geometry_builder.py:106: ev_by={clean(x.get('listing_id')):x.get('evidence',{}) for x in ev_items}
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\estimated_candidate_geometry_builder.py:107: docs_by={clean(x.get('listing_id')):x for x in read_csv(exports/'full_autonomous_public_docs_top80_review.csv')}
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\estimated_candidate_geometry_builder.py:110: exact_by.setdefault(clean(r0.get('listing_id')),[]).append(r0)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\estimated_candidate_geometry_builder.py:113: lid=clean(q.get('listing_id'))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\estimated_candidate_geometry_builder.py:117: if clean(q.get(k)): lon=float(clean(q.get(k))); break
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\estimated_candidate_geometry_builder.py:121: if clean(q.get(k)): lat=float(clean(q.get(k))); break
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\estimated_candidate_geometry_builder.py:123: fr=ring(parse_gj(clean(q.get('feed_polygon_geojson'))))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\export_final_after_d_upgrade.py:42: "verified_original_count": sum(1 for r in rows if r.get("confidence_tier") == "A"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\export_final_after_d_upgrade.py:43: "a_question_count": sum(1 for r in rows if r.get("confidence_tier") == "A?"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\export_final_after_d_upgrade.py:71: f"<td><b>{esc(r.get('listing_id'))}</b><br>{esc(r.get('postcode'))}<br>"
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\export_final_after_d_upgrade.py:72: f"<a href=\"{esc(r.get('listing_url'))}\" target=\"_blank\">listing</a></td>"
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\export_final_after_d_upgrade.py:73: f"<td><b>{esc(r.get('confidence_tier'))}</b><br>{esc(r.get('confidence_score'))}/100<br>"
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\export_final_after_d_upgrade.py:74: f"{esc(r.get('confidence_label'))}<br>{esc(r.get('source_level'))}</td>"
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\export_final_after_d_upgrade.py:75: f"<td>area={esc(r.get('source_area'))}<br>plan={esc(r.get('plan_signal'))}<br>"
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\export_final_after_d_upgrade.py:76: f"doc={esc(r.get('public_doc_downloaded'))}<br>ref={esc(r.get('reference_signal'))}<br>"
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\export_final_after_d_upgrade.py:77: f"polygon={esc(r.get('polygon_signal'))}</td>"
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\export_final_after_d_upgrade.py:78: f"<td>area={esc(r.get('estimated_area_m2'))} m²<br>"
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\export_final_after_d_upgrade.py:79: f"perimeter={esc(r.get('perimeter_m'))} m<br>"
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\export_final_after_d_upgrade.py:80: f"m={esc(r.get('side_lengths_m_json'))}<br>"
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\export_market_listing_parcel_package.py:193: metadata = _to_metadata_dict(row.get("metadata_json"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\export_market_listing_parcel_package.py:196: parcel_geojson = parse_geojson_value(row.get("parcel_geom_geojson"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\export_market_listing_parcel_package.py:197: parcel_geojson_metric = parse_geojson_value(row.get("parcel_geom_metric_geojson"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\export_market_listing_parcel_package.py:209: raise ValueError(f"Parcel geometry missing or invalid for listing_id={row.get('listing_id')}")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\export_market_listing_parcel_package.py:229: "listing_id": row.get("listing_id"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\export_market_listing_parcel_package.py:230: "provider_listing_id": row.get("provider_listing_id"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\export_market_listing_parcel_package.py:231: "matched_parcel_id": row.get("matched_parcel_id"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\export_market_listing_parcel_package.py:232: "matched_parcel_ref": row.get("matched_parcel_ref"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\export_market_listing_parcel_package.py:233: "matched_inspire_id": row.get("matched_inspire_id"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\export_market_listing_parcel_package.py:234: "listing_url": row.get("listing_url"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\export_market_listing_parcel_package.py:235: "source_url": row.get("source_url"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\export_market_listing_parcel_package.py:243: parcel_perimeter_m = _to_float(row.get("parcel_perimeter_m"), 3) or round(sum(parcel_edges_m), 3)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\fill_market_listing_export_gaps.py:46: price = _to_float(row.get("ask_price"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\fill_market_listing_export_gaps.py:49: authority = (row.get("local_authority") or "").strip()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\fill_market_listing_export_gaps.py:63: direct = _to_float(row.get("ask_price"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\fill_market_listing_export_gaps.py:66: authority = (row.get("local_authority") or "").strip()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\fill_market_listing_export_gaps.py:75: area_m2 = _to_float(row.get("listing_area_m2"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\fill_market_listing_export_gaps.py:76: area_acres = _to_float(row.get("listing_area_acres"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\fill_market_listing_export_gaps.py:82: parcel_area = _to_float(row.get("parcel_area_m2"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\fill_market_listing_export_gaps.py:89: lat = _to_float(row.get("listing_point_lat"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\fill_market_listing_export_gaps.py:90: lon = _to_float(row.get("listing_point_lon"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\fill_market_listing_export_gaps.py:91: x = _to_float(row.get("listing_point_x"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\fill_market_listing_export_gaps.py:92: y = _to_float(row.get("listing_point_y"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\fill_market_listing_export_gaps.py:98: centroid_lat = _to_float(row.get("parcel_centroid_lat"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\final_3110_fail_closed_l4_pipeline.py:186: geo_type = clean(geojson.get("type"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\final_3110_fail_closed_l4_pipeline.py:187: coords = geojson.get("coordinates")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\final_3110_fail_closed_l4_pipeline.py:314: listing_id = clean(row.get(key))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\final_3110_fail_closed_l4_pipeline.py:331: val = clean(row.get(key))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\final_3110_fail_closed_l4_pipeline.py:338: val = clean(row.get(key))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\final_3110_fail_closed_l4_pipeline.py:363: verified_geojson = parse_geojson(row.get("verified_polygon_geojson"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\final_3110_fail_closed_l4_pipeline.py:364: decision = clean(row.get("final_polygon_decision")).lower()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\final_3110_fail_closed_l4_pipeline.py:365: confidence = clean(row.get("confidence")).lower()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\final_3110_fail_closed_l4_pipeline.py:373: clean(row.get("boundary_evidence_type")) or "planning_portal_georef_boundary",
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\final_3110_fail_closed_l4_pipeline.py:374: clean(row.get("verification_note")) or "High confidence original-site georeferenced boundary from public planning records.",
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\final_3110_fail_closed_l4_pipeline.py:376: clean(row.get("matched_application_url") or row.get("documents_tab_url") or row.get("portal_search_url")),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\final_3110_fail_closed_l4_pipeline.py:381: clean(row.get("boundary_evidence_type")) or "planning_portal_georef_boundary",
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\find_deep_apply_db_matches.py:21: ids = [r.get("listing_id", "").strip() for r in rows if r.get("listing_id")]
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\find_deep_apply_db_matches.py:24: urls = [(r.get("verification_source_url") or "").strip() for r in rows if r.get("verification_source_url")]
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\find_deep_apply_db_matches.py:145: w.writerow({k: r.get(k) for k in fields})
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\full_autonomous_polygon_classifier.py:56: public_by_id = {clean(r.get("listing_id")): r for r in public}
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\full_autonomous_polygon_classifier.py:57: docs_by_id = {clean(r.get("listing_id")): r for r in docs}
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\full_autonomous_polygon_classifier.py:61: exact_by_id.setdefault(clean(r.get("listing_id")), []).append(r)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\full_autonomous_polygon_classifier.py:68: lid = clean(q.get("listing_id"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\full_autonomous_polygon_classifier.py:69: p = public_by_id.get(lid, {})
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\full_autonomous_polygon_classifier.py:70: d = docs_by_id.get(lid, {})
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\full_autonomous_polygon_classifier.py:71: e_rows = exact_by_id.get(lid, [])
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\full_autonomous_polygon_classifier.py:77: source_url = clean(q.get("listing_url"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\full_autonomous_polygon_classifier.py:81: doc_paths = clean(d.get("downloaded_pdf_paths")) or clean(d.get("downloaded_image_paths"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\full_autonomous_polygon_classifier.py:86: planning_ref = planning_ref or clean(e.get("planning_ref"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\full_autonomous_polygon_classifier.py:87: e_decision = clean(e.get("final_polygon_decision")).lower()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\full_autonomous_polygon_classifier.py:88: e_conf = clean(e.get("confidence")).lower()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\import_final_sale_geometry_confidence_table.py:63: }.get(clean(tier), 0)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\import_final_sale_geometry_confidence_table.py:66: tier = clean(row.get("deep_confidence_tier") or row.get("strict_confidence_tier") or row.get("confidence_tier") or row.get("confidence_level"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\import_final_sale_geometry_confidence_table.py:67: score = as_int(row.get("deep_confidence_score") or row.get("strict_confidence_score") or row.get("confidence_score"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\import_final_sale_geometry_confidence_table.py:71: label = clean(row.get("deep_confidence_label") or row.get("strict_confidence_label") or row.get("confidence_label") or row.get("generation_method"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\import_final_sale_geometry_confidence_table.py:72: note = clean(row.get("deep_verification_note") or row.get("strict_verification_note") or row.get("verification_note"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\import_final_sale_geometry_confidence_table.py:75: "listing_id": clean(row.get("listing_id")),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\import_final_sale_geometry_confidence_table.py:76: "provider_listing_id": clean(row.get("provider_listing_id")),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\import_final_sale_geometry_confidence_table.py:77: "listing_url": clean(row.get("listing_url") or row.get("verification_source_url")),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\import_final_sale_geometry_confidence_table.py:78: "ask_price": clean(row.get("ask_price")),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\import_final_sale_geometry_confidence_table.py:79: "postcode": clean(row.get("postcode")),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\import_final_sale_geometry_confidence_table.py:80: "local_authority": clean(row.get("local_authority")),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\import_final_sale_geometry_confidence_table.py:87: "source_area": clean(row.get("source_area") or row.get("source_text_area")),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\load_external_market_sales_evidence.py:45: if n in row and str(row.get(n) or "").strip():
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\load_external_market_sales_evidence.py:46: return str(row.get(n) or "").strip()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\load_external_market_sales_evidence.py:263: w.writerow({k: r.get(k) for k in fields})
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_autonomous_polygon_finalize.py:65: decision = _clean(row.get("final_polygon_decision") or row.get("current_decision")).lower()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_autonomous_polygon_finalize.py:66: confidence = _clean(row.get("confidence") or row.get("current_confidence")).lower()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_autonomous_polygon_finalize.py:67: verified = _clean(row.get("verified_polygon_geojson"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_autonomous_polygon_finalize.py:96: queue_by_id = {r.get("listing_id", ""): r for r in queue_rows}
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_autonomous_polygon_finalize.py:110: listing_id = _clean(row.get("listing_id"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_autonomous_polygon_finalize.py:112: base = queue_by_id.get(listing_id, {})
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_autonomous_polygon_finalize.py:115: "provider_listing_id": _clean(base.get("provider_listing_id")),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_autonomous_polygon_finalize.py:116: "listing_url": _clean(row.get("listing_url") or base.get("listing_url")),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_autonomous_polygon_finalize.py:117: "postcode": _clean(row.get("postcode") or base.get("postcode")),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_autonomous_polygon_finalize.py:118: "local_authority": _clean(row.get("local_authority") or base.get("local_authority")),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_autonomous_polygon_finalize.py:119: "planning_ref": _clean(row.get("planning_ref")),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_autonomous_polygon_finalize.py:123: "candidate_polygon_geojson": _clean(row.get("candidate_polygon_geojson")),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_deep_sales_source_confidence_booster.py:73: r = requests.get(url, headers=headers, timeout=25)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_deep_sales_source_confidence_booster.py:137: r = requests.get(url, headers={"User-Agent": "Mozilla/5.0 candidate-sale-geometry-evidence/1.0"}, timeout=35)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_deep_sales_source_confidence_booster.py:139: ctype = r.headers.get("content-type", "").lower()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_deep_sales_source_confidence_booster.py:185: lid = clean(r.get("listing_id"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_deep_sales_source_confidence_booster.py:192: lid = clean(row.get("listing_id"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_deep_sales_source_confidence_booster.py:193: downloaded_urls = [d["url"] for d in downloaded if d.get("path")]
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_deep_sales_source_confidence_booster.py:194: downloaded_names = " ".join(downloaded_urls + [d.get("path", "") for d in downloaded])
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_deep_sales_source_confidence_booster.py:195: combined = " ".join([page_text or "", downloaded_names, clean(prev.get("evidence_explanation")), clean(prev.get("verification_note")), clean(prev.get("strict_verification_note"))])
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_deep_sales_source_confidence_booster.py:198: source_area = bool(page_area_hits) or clean(prev.get("source_text_area")).lower() == "yes" or clean(prev.get("area_source")).lower() in {"source_text_area", "public_site_area_text"}
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_deep_sales_source_confidence_booster.py:200: ref_signal = has_reference_signal(combined) or clean(prev.get("planning_ref")).lower() == "yes" or clean(prev.get("lot_ref")).lower() == "yes" or clean(prev.get("title_ref")).lower() == "yes"
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_deep_sales_source_confidence_booster.py:201: doc_signal = bool(downloaded_urls) or clean(prev.get("public_doc_or_image")).lower() == "yes" or clean(prev.get("doc_evidence_available")).lower() == "yes"
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_deep_sales_source_confidence_booster.py:227: prev_score = int(float(clean(prev.get("strict_confidence_score")) or "0"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_market_polygon_verification_batch.py:61: raw_record = metadata.get("raw_record") if isinstance(metadata.get("raw_record"), dict) else {}
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_market_polygon_verification_batch.py:62: match_hints = metadata.get("match_hints") if isinstance(metadata.get("match_hints"), dict) else {}
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_market_polygon_verification_batch.py:65: parsed = _parse_geojson(scope.get(key))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_market_polygon_verification_batch.py:87: geo_type = _clean(geojson.get("type"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_market_polygon_verification_batch.py:88: coords = geojson.get("coordinates")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_market_polygon_verification_batch.py:161: current = best_by_key.get(key)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_market_polygon_verification_batch.py:245: raw_record = metadata.get("raw_record") if isinstance(metadata.get("raw_record"), dict) else {}
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_market_polygon_verification_batch.py:246: current_status = _clean(raw_record.get("source_polygon_original_site_status")) or _clean(
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_market_polygon_verification_batch.py:247: metadata.get("source_polygon_original_site_status")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_market_polygon_verification_batch.py:251: source_origin = _clean(raw_record.get("source_polygon_origin")) or _clean(metadata.get("source_polygon_origin"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_market_polygon_verification_batch.py:256: match = link_map.get(_clean(row.listing_id), {})
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_market_polygon_verification_batch.py:269: "matched_parcel_ref": _clean(match.get("matched_parcel_ref")),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_planning_ref_docs_review.py:116: css = "ok" if _clean(row.get("verified_polygon_geojson")) else "warn"
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_planning_ref_docs_review.py:119: for url in _clean(row.get("downloaded_doc_urls")).split(" | ")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_planning_ref_docs_review.py:122: portal = _clean(row.get("planning_portal_url"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_planning_ref_docs_review.py:126: f"<td>{html.escape(_clean(row.get('listing_id')))}<br>{html.escape(_clean(row.get('postcode')))}<br>{html.escape(_clean(row.get('local_authority')))}</td>"
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_planning_ref_docs_review.py:127: f"<td>{html.escape(_clean(row.get('planning_ref')))}</td>"
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_planning_ref_docs_review.py:130: f"<td>{html.escape(_clean(row.get('final_polygon_decision')))} / {html.escape(_clean(row.get('confidence')))}<br>{html.escape(_clean(row.get('boundary_evidence_type')))}</td>"
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_planning_ref_docs_review.py:131: f"<td>{html.escape(_clean(row.get('verification_note')))}<br><b>Next:</b> {html.escape(_clean(row.get('next_action')))}</td>"
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_planning_ref_docs_review.py:176: href = _clean(attr.get("href"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_planning_ref_docs_review.py:205: "url": meta.get("resolved_url", url),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_planning_ref_docs_review.py:206: "status": int(meta.get("status", 0) or 0),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_planning_ref_docs_review.py:207: "content_type": _clean(meta.get("content_type")),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_planning_ref_docs_review.py:210: "error": _clean(meta.get("error")),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_polygon_accuracy_diagnostic.py:89: nearest = _parse_float(row.get("nearest_distance_m"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_polygon_accuracy_diagnostic.py:90: inside = str(row.get("nearest_contains_point", "")).lower() == "true"
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_polygon_accuracy_diagnostic.py:128: local_authorities = sorted({_clean(row.get("local_authority")) for row in selected_rows if _clean(row.get("local_authority"))})
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_polygon_accuracy_diagnostic.py:153: listing_id = _clean(src.get("listing_id"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_polygon_accuracy_diagnostic.py:154: lon = _parse_float(src.get("centroid_lon"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_polygon_accuracy_diagnostic.py:155: lat = _parse_float(src.get("centroid_lat"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_polygon_accuracy_diagnostic.py:159: "provider_listing_id": _clean(src.get("provider_listing_id")),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_polygon_accuracy_diagnostic.py:160: "listing_url": _clean(src.get("listing_url")),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_polygon_accuracy_diagnostic.py:161: "local_authority": _clean(src.get("local_authority")),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_polygon_accuracy_diagnostic.py:162: "postcode": _clean(src.get("postcode")),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_polygon_accuracy_diagnostic.py:163: "ask_price": _clean(src.get("ask_price")),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_polygon_accuracy_diagnostic.py:166: "feed_polygon_rectangular_like": _clean(src.get("feed_polygon_rectangular_like")),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_polygon_candidate_generator.py:108: context = str(item.get("context", ""))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_polygon_candidate_generator.py:114: return (-score, float(item.get("m2") or 0))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_polygon_candidate_generator.py:117: return float(chosen["m2"]), f"{chosen.get('raw')} | {chosen.get('context')}"
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_polygon_candidate_generator.py:123: typ = _clean(geojson.get("type"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_polygon_candidate_generator.py:124: coords = geojson.get("coordinates")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_polygon_candidate_generator.py:203: if tag.lower() == "a" and attr.get("href"):
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_polygon_candidate_generator.py:204: self._href = attr.get("href")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_polygon_candidate_generator.py:207: if attr.get(key):
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_polygon_candidate_generator.py:225: r = requests.get(url, headers={"User-Agent": UA, "Accept": "text/html,application/xhtml+xml,*/*"}, timeout=timeout)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_polygon_candidate_generator.py:226: ctype = r.headers.get("content-type", "")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_polygon_candidate_generator.py:328: "evidence_urls": [p["url"] for p in pages if p.get("url")],
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_polygon_candidate_generator.py:341: distance = float(c.get("distance_m") or 999999.0)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_polygon_srid_postcode_diagnostic.py:110: listing_pc = _clean(row.get("postcode")).upper()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_polygon_srid_postcode_diagnostic.py:114: la = _clean(row.get("local_authority")).lower()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_polygon_srid_postcode_diagnostic.py:210: listing_id = _clean(row.get("listing_id"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_polygon_srid_postcode_diagnostic.py:211: lon = _parse_float(row.get("centroid_lon"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_polygon_srid_postcode_diagnostic.py:212: lat = _parse_float(row.get("centroid_lat"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_polygon_srid_postcode_diagnostic.py:213: pc = _clean(row.get("postcode")).upper()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_polygon_srid_postcode_diagnostic.py:215: la = _clean(row.get("local_authority"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_polygon_srid_postcode_diagnostic.py:220: "listing_url": _clean(row.get("listing_url")),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_polygon_srid_postcode_diagnostic.py:303: "listing_url": _clean(row.get("listing_url")),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_polygon_srid_postcode_diagnostic.py:318: candidate_payloads.sort(key=lambda x: (-_parse_float(x.get("candidate_score")) if _parse_float(x.get("candidate_score")) is not None else 0, _parse_float(x.get("distance_m")) or 999999))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_polygon_srid_postcode_diagnostic.py:338: if rank == 1 and c.get("candidate_polygon_geojson"):
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_public_polygon_source_batch.py:132: raw_record = metadata.get("raw_record") if isinstance(metadata.get("raw_record"), dict) else {}
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_public_polygon_source_batch.py:145: payload = _parse_json(scope.get(key))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_public_polygon_source_batch.py:162: geo_type = _clean(geojson.get("type"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_public_polygon_source_batch.py:163: coords = geojson.get("coordinates")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_public_polygon_source_batch.py:337: listing_ids = [_clean(r.get("listing_id")) for r in rows if _clean(r.get("listing_id"))]
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_public_polygon_source_batch.py:344: listing_id = _clean(row.get("listing_id"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_public_polygon_source_batch.py:345: metadata = metadata_map.get(listing_id, {})
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_public_polygon_source_batch.py:346: raw_record = metadata.get("raw_record") if isinstance(metadata.get("raw_record"), dict) else {}
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_public_polygon_source_batch.py:352: _clean(row.get("listing_url")),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_public_polygon_source_batch.py:353: _clean(row.get("postcode")),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_public_polygon_source_batch.py:354: _clean(row.get("local_authority")),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_public_polygon_source_batch.py:355: _clean(row.get("ask_price")),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_real_site_polygon_verifier.py:23: from shapely.ops import transform as shapely_transform
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_real_site_polygon_verifier.py:113: response = requests.get(
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_real_site_polygon_verifier.py:216: geo_type = clean(value.get("type"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_real_site_polygon_verifier.py:217: coords = value.get("coordinates")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_real_site_polygon_verifier.py:220: if geo_type == "Feature" and isinstance(value.get("geometry"), dict):
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_real_site_polygon_verifier.py:221: return normalize_geojson_candidate(value.get("geometry"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_real_site_polygon_verifier.py:222: if isinstance(value.get("geometry"), dict):
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_real_site_polygon_verifier.py:223: return normalize_geojson_candidate(value.get("geometry"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_real_site_polygon_verifier.py:230: geo_type = clean(geojson.get("type"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_real_site_polygon_verifier.py:231: coords = geojson.get("coordinates")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_real_site_polygon_verifier.py:470: if listing_area_m2 is not None and best.get("area_ratio_delta") is not None and best["area_ratio_delta"] > max_area_ratio_delta:
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_real_site_polygon_verifier.py:489: listing_id = clean(row.get("listing_id")) or clean(row.get("provider_listing_id"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_site_derived_polygon_miner.py:105: geo_type = _clean(geojson.get("type"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_site_derived_polygon_miner.py:106: coords = geojson.get("coordinates")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_site_derived_polygon_miner.py:188: if tag.lower() == "a" and attr.get("href"):
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_site_derived_polygon_miner.py:189: self._current_href = attr.get("href")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_site_derived_polygon_miner.py:192: if attr.get(key):
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_site_derived_polygon_miner.py:211: resp = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_site_derived_polygon_miner.py:212: ctype = resp.headers.get("content-type", "")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_site_derived_polygon_miner.py:302: strong_site_evidence = bool(evidence.get("has_plot_words")) and (
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_site_derived_polygon_miner.py:303: bool(evidence.get("postcodes")) or bool(evidence.get("lot_refs")) or bool(evidence.get("planning_refs"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_site_derived_polygon_miner.py:348: for source in site_evidence.get("sources", []):
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_site_derived_polygon_miner.py:349: all_areas.extend(source.get("evidence", {}).get("areas", []))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_site_derived_polygon_miner.py:354: context = str(item.get("context", ""))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\manifests.py:37: if isinstance(payload, dict) and isinstance(payload.get('records'), list):
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\manifests.py:69: slugify(str(row.get('local_authority') or '')): row for row in (existing_manifest_rows or []) if row.get('local_authority')
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\manifests.py:72: seed_by_authority = {slugify(str(row.get('local_authority') or '')): row for row in seed_records if row.get('local_authority')}
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\manifests.py:75: raw_authority = str(row.get('local_authority') or row.get('organisation') or '').strip()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\manifests.py:76: raw_props = (row.get('metadata_json') or {}).get('raw_properties') if isinstance(row.get('metadata_json'), dict) else {}
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\manifests.py:77: site_plan_url = str(row.get('site_plan_url') or '').strip()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\manifests.py:103: _append_unique(evidence['sample_source_record_ids'], str(row.get('site_id') or row.get('reference') or ''), max_items=5)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\manifests.py:104: _append_unique(evidence['organisation_entities'], str(raw_props.get('organisation-entity') or row.get('organisation') or ''), max_items=5)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\manifests.py:110: authority = str(seed_row.get('local_authority') or '').strip()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\manifests.py:114: existing = existing_by_authority.get(authority_key, {})
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\manifests.py:115: evidence = evidence_by_authority.get(authority_key, {})
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\manifests.py:116: source_url = str(existing.get('source_url') or seed_row.get('source_url') or '').strip()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\match_external_market_polygons_to_parcels.py:23: typ = obj.get("type")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\match_external_market_polygons_to_parcels.py:26: geom = obj.get("geometry")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\match_external_market_polygons_to_parcels.py:31: for feat in obj.get("features") or []:
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\match_external_market_polygons_to_parcels.py:32: geom = feat.get("geometry")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\match_external_market_polygons_to_parcels.py:99: raw_geojson = row.get("verified_polygon_geojson") or ""
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\match_external_market_polygons_to_parcels.py:104: "listing_id": (row.get("listing_id") or "").strip(),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\match_external_market_polygons_to_parcels.py:105: "verification_status": (row.get("verification_status") or "").strip(),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\match_external_market_polygons_to_parcels.py:106: "verification_source_url": (row.get("verification_source_url") or "").strip(),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\match_external_market_polygons_to_parcels.py:107: "verification_note": (row.get("verification_note") or "").strip(),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\match_external_market_polygons_to_parcels.py:301: r.get("source_url"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\match_external_market_polygons_to_parcels.py:302: r.get("verification_status"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\match_external_market_polygons_to_parcels.py:303: r.get("polygon_overlap_ratio"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\orchestrator.py:138: format_hint=row.get('format_hint'),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\orchestrator.py:139: is_active=bool(row.get('is_active', True)),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\orchestrator.py:140: last_checked_at=_parse_datetime(row.get('last_checked_at')),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\orchestrator.py:141: notes=row.get('notes'),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\orchestrator.py:171: 'parcel_ref': row.get('parcel_ref', row['inspire_id']),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\orchestrator.py:172: 'local_authority': row.get('local_authority'),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\orchestrator.py:173: 'source_month': _parse_date(row.get('source_month')),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\orchestrator.py:174: 'postcode': row.get('postcode'),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\orchestrator.py:175: 'address_text': row.get('address_text'),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\orchestrator.py:177: 'centroid': wkt_to_element(row.get('centroid_wkt')),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\orchestrator.py:178: 'area_m2': float(row['area_m2']) if row.get('area_m2') is not None else None,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\orchestrator.py:179: 'perimeter_m': float(row['perimeter_m']) if row.get('perimeter_m') is not None else None,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\planning_ref_exact_doc_download.py:89: css = "ok" if _clean(row.get("verified_polygon_geojson")) else "warn"
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\planning_ref_exact_doc_download.py:92: for u in _clean(row.get("downloaded_doc_urls")).split(" | ")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\planning_ref_exact_doc_download.py:97: f"<td>{html.escape(_clean(row.get('listing_id')))}<br>{html.escape(_clean(row.get('local_authority')))} {html.escape(_clean(row.get('postcode')))}</td>"
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\planning_ref_exact_doc_download.py:98: f"<td>{html.escape(_clean(row.get('planning_ref')))}</td>"
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\planning_ref_exact_doc_download.py:99: f"<td><a href='{html.escape(_clean(row.get('portal_search_url')))}' target='_blank'>{html.escape(_clean(row.get('portal_search_url')))}</a></td>"
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\planning_ref_exact_doc_download.py:100: f"<td>{html.escape(_clean(row.get('matched_application_url')))}<br>{html.escape(_clean(row.get('documents_tab_url')))}</td>"
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\planning_ref_exact_doc_download.py:102: f"<td>{html.escape(_clean(row.get('final_polygon_decision')))} / {html.escape(_clean(row.get('confidence')))}<br>{html.escape(_clean(row.get('boundary_evidence_type')))}</td>"
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\planning_ref_exact_doc_download.py:103: f"<td>{html.escape(_clean(row.get('verification_note')))}<br><b>Next:</b> {html.escape(_clean(row.get('next_action')))}</td>"
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\planning_ref_exact_doc_download.py:131: "url": _clean(meta.get("resolved_url")) or url,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\planning_ref_exact_doc_download.py:132: "status": int(meta.get("status", 0) or 0),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\planning_ref_exact_doc_download.py:133: "content_type": _clean(meta.get("content_type")),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\planning_ref_exact_doc_download.py:136: "error": _clean(meta.get("error")),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\prefetch_hmlr_inspire_zips.py:25: if str(row.get("country") or "").strip().lower() == "england"
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\prefetch_hmlr_inspire_zips.py:36: zip_name = str(record.get("zip_name") or Path(zip_url).name)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\prefetch_hmlr_inspire_zips.py:39: response = session.get(zip_url, timeout=settings.http_timeout_s)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\prefetch_hmlr_inspire_zips.py:49: "authority": record.get("authority"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\prepare_homes_england_handoff.py:53: authority = str(state.get("current_authority") or "").strip()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\prepare_homes_england_handoff.py:54: offset = state.get("current_offset")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\prepare_homes_england_handoff.py:118: heartbeat = _parse_iso_timestamp(payload.get("heartbeat_at")) or _parse_iso_timestamp(payload.get("started_at"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\prepare_homes_england_handoff.py:166: if str(row.get("country") or "").strip().lower() == "england"
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\prepare_homes_england_handoff.py:173: zip_name = str(record.get("zip_name") or Path(zip_url).name)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\prepare_homes_england_handoff.py:177: response = session.get(zip_url, timeout=settings.http_timeout_s)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\prepare_homes_england_handoff.py:181: "authority": record.get("authority"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\prepare_repo_manual_match_batch.py:32: r"C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\data\live_feeds\drops\market\repo_manual_match_batch_immediate.csv"
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\prepare_repo_manual_match_batch.py:35: r"C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\data\live_feeds\drops\market\repo_manual_match_batch_authority_expansion.csv"
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\prepare_repo_manual_match_batch.py:85: return bool((row.get("matched_parcel_ref") or "").strip() or (row.get("matched_inspire_id") or "").strip())
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\prepare_repo_manual_match_batch.py:91: authority = (row.get("local_authority") or "").strip()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\prepare_repo_manual_match_batch.py:92: postcode = (row.get("postcode") or "").strip()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\prepare_repo_manual_match_batch.py:93: title = (row.get("title") or "").lower()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\prepare_repo_manual_match_batch.py:94: notes = (row.get("location_notes") or "").lower()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\prepare_repo_manual_match_batch.py:95: url = (row.get("listing_url") or "").lower()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\prepare_repo_manual_match_batch.py:108: if (row.get("site_area_m2") or "").strip() or (row.get("site_area_acres") or "").strip():
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\prepare_repo_manual_match_batch.py:136: if row.get("listing_id", "").startswith("AG-") and not authority:
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\prepare_repo_manual_match_batch.py:176: listing_id = (row.get("listing_id") or "").strip()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\prepare_repo_manual_match_batch.py:186: authority = (row.get("local_authority") or "").strip()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\prepare_repo_market_feed.py:16: r"C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\data\live_feeds\drops\market\repo_master_market_input_matched_only.csv"
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\prepare_repo_market_feed.py:19: r"C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\data\live_feeds\drops\market\repo_master_market_input_delta.csv"
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\prepare_repo_market_feed.py:31: return bool((row.get("matched_parcel_ref") or "").strip() or (row.get("matched_inspire_id") or "").strip())
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\prepare_repo_market_feed.py:38: listing_id = (row.get("listing_id") or "").strip()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\prepare_repo_market_feed.py:76: delta_rows = [row for row in matched_only if (row.get("listing_id") or "").strip() not in existing_ids]
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\prepare_repo_review_needed_candidates.py:15: r"C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\data\live_feeds\drops\market\repo_archive_union_market_input.csv"
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\prepare_repo_review_needed_candidates.py:18: r"C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\data\live_feeds\drops\market\repo_review_needed_candidate_batch.csv"
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\prepare_repo_review_needed_candidates.py:103: title = _clean_title(row.get("title") or "")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\prepare_repo_review_needed_candidates.py:104: url_context = _slug_context(row.get("listing_url") or "")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\prepare_repo_review_needed_candidates.py:111: listing_id = _clean(row.get("listing_id"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\prepare_repo_review_needed_candidates.py:114: url = (row.get("listing_url") or "").lower()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\prepare_repo_review_needed_candidates.py:117: title = _clean_title(row.get("title") or "")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\prepare_repo_review_needed_candidates.py:120: title_lower = (row.get("title") or "").lower()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\prepare_repo_review_needed_candidates.py:121: url_lower = (row.get("listing_url") or "").lower()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\prepare_repo_review_needed_candidates.py:128: title = _clean(row.get("title"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\prepare_repo_review_needed_candidates.py:135: url_context = _slug_context(row.get("listing_url") or "")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\prepare_repo_review_needed_candidates.py:138: review_reason = _clean(row.get("review_reason"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\prioritize_homes_england_authorities.py:44: records = manifest.get('records', [])
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\prioritize_homes_england_authorities.py:82: canonical = canonicalize_authority(str(record.get('authority') or ''))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\prioritize_homes_england_authorities.py:87: 'authority': record.get('authority'),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\prioritize_homes_england_authorities.py:88: 'zip_url': record.get('zip_url'),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\prioritize_homes_england_authorities.py:95: manifest_match = manifest_by_canonical.get(canonical or '')
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\prioritize_homes_england_authorities.py:102: 'manifest_offset': manifest_match.get('offset') if manifest_match else None,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\prioritize_homes_england_authorities.py:103: 'manifest_authority': manifest_match.get('authority') if manifest_match else None,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\prioritize_homes_england_authorities.py:104: 'zip_url': manifest_match.get('zip_url') if manifest_match else None,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\process_repo_market_delta.py:33: delta_rows = [row for row in matched_only if (row.get("listing_id") or "").strip() not in existing_ids]
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\process_repo_market_delta.py:47: providers = payload.get("providers") or []
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\process_repo_market_delta.py:51: provider_copy["active"] = provider_copy.get("provider_name") == DELTA_PROVIDER_NAME
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\public_polygon_docs_top30_review.py:51: ev = item.get("evidence", {})
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\public_polygon_docs_top30_review.py:52: links = ev.get("public_links", [])
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\public_polygon_docs_top30_review.py:53: imgs = ev.get("public_images", [])
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\public_polygon_docs_top30_review.py:55: if ev.get("planning_refs"):
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\public_polygon_docs_top30_review.py:57: if ev.get("title_refs"):
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\public_polygon_docs_top30_review.py:59: if ev.get("lot_refs"):
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\public_polygon_docs_top30_review.py:61: if ev.get("areas"):
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\public_polygon_docs_top30_review.py:63: if any(PDF_RE.search((x.get("url", "") + " " + x.get("label", ""))) for x in links):
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\public_polygon_docs_top30_review.py:65: if any(PLAN_HIT_RE.search((x.get("url", "") + " " + x.get("label", ""))) for x in links):
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\public_polygon_docs_top30_review.py:67: if any(IMAGE_RE.search((x.get("url", "") + " " + x.get("alt", ""))) for x in imgs):
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\public_polygon_docs_top30_review.py:69: if ev.get("geojson_candidates"):
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\public_polygon_docs_top30_review.py:93: ctype = json.loads(meta.read_text(encoding="utf-8")).get("content_type", "")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\rebuild_parcel_use_cache.py:107: mapped = SCENARIO_TO_FIVE_COLOR_LABEL.get(best_profile)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\rebuild_parcel_use_cache.py:267: context_summary = context_map.get(parcel_id)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\rebuild_parcel_use_cache.py:268: scenario_scores = score_map.get(parcel_id, [])
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\rebuild_parcel_use_cache.py:270: label = str(parcel_use.get("label") or "unknown")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\rebuild_parcel_use_cache.py:271: confidence = float(parcel_use.get("confidence") or 0.0)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\rebuild_parcel_use_cache.py:272: evidence = dict(parcel_use.get("evidence") or {})
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\rebuild_parcel_use_targeted_signal_scope.py:308: context_summary = context_map.get(parcel_id)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\rebuild_parcel_use_targeted_signal_scope.py:309: scenario_scores = score_map.get(parcel_id, [])
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\rebuild_parcel_use_targeted_signal_scope.py:311: source_label = str(parcel_use.get("label") or "unknown").strip().lower() or "unknown"
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\rebuild_parcel_use_targeted_signal_scope.py:313: evidence = dict(parcel_use.get("evidence") or {})
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\rebuild_parcel_use_targeted_signal_scope.py:314: confidence_value = float(parcel_use.get("confidence") or 0.0)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\rebuild_parcel_use_targeted_signal_scope.py:318: signal_payload = signal_map.get(int(parcel_id), {})
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\rebuild_parcel_use_targeted_signal_scope.py:320: signal_payload.get("source_summary"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\rebuild_parcel_use_targeted_signal_scope.py:321: int(signal_payload.get("history_transaction_count") or 0),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\restore_sale_geometry_confidence_results_from_final_csv.py:120: lid = clean(r.get("listing_id"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\restore_sale_geometry_confidence_results_from_final_csv.py:126: "provider_listing_id": clean(r.get("provider_listing_id")),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\restore_sale_geometry_confidence_results_from_final_csv.py:127: "listing_url": clean(r.get("listing_url")),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\restore_sale_geometry_confidence_results_from_final_csv.py:128: "ask_price": clean(r.get("ask_price")),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\restore_sale_geometry_confidence_results_from_final_csv.py:129: "postcode": clean(r.get("postcode")),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\restore_sale_geometry_confidence_results_from_final_csv.py:130: "local_authority": clean(r.get("local_authority")),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\restore_sale_geometry_confidence_results_from_final_csv.py:131: "confidence_score": as_int(r.get("confidence_score")),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\restore_sale_geometry_confidence_results_from_final_csv.py:132: "confidence_tier": clean(r.get("confidence_tier")),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\restore_sale_geometry_confidence_results_from_final_csv.py:133: "confidence_label": clean(r.get("confidence_label")),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\restore_sale_geometry_confidence_results_from_final_csv.py:134: "source_level": clean(r.get("source_level")),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\restore_sale_geometry_confidence_results_from_final_csv.py:135: "geometry_status": clean(r.get("geometry_status")),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\restore_sale_geometry_confidence_results_from_final_csv.py:136: "is_verified_original": clean(r.get("is_verified_original")),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\run_cost_engine_pilot.py:130: for row in output.get("estimates", []):
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\run_cost_engine_pilot.py:131: breakdown = row.get("breakdown") if isinstance(row, dict) else {}
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\run_cost_engine_pilot.py:134: "estimate_id": row.get("estimate_id"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\run_cost_engine_pilot.py:135: "parcel_id": row.get("parcel_id"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\run_cost_engine_pilot.py:136: "building_type": row.get("building_type"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\run_cost_engine_pilot.py:137: "spec_grade": row.get("spec_grade"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\run_cost_engine_pilot.py:138: "region": row.get("region"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\run_cost_engine_pilot.py:139: "total_cost_gbp": (breakdown or {}).get("total_cost"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\run_cost_engine_pilot.py:140: "cost_per_gia_m2": (breakdown or {}).get("cost_per_gia_m2"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\run_cost_engine_pilot.py:141: "confidence_score": row.get("confidence_score"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\run_cost_engine_pilot.py:142: "confidence_band": row.get("confidence_band"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\run_cost_engine_pilot.py:143: "is_seed_based": row.get("is_seed_based"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\run_hmlr_inspire_low_disk.py:38: help='Stop before the next authority batch if free disk drops below this threshold.',
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\run_hmlr_inspire_low_disk.py:50: if str(row.get('country') or '').strip().lower() == 'england'
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\run_hmlr_inspire_low_disk.py:57: if any(pattern in str(row.get('authority') or '').strip().lower() for pattern in patterns)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\run_hmlr_inspire_low_disk.py:112: last_run_id=str(run_summary.get('run_id') or ''),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\run_hmlr_inspire_low_disk.py:124: last_run_id=str(run_summary.get('run_id') or ''),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\run_hmlr_inspire_low_disk.py:141: authority = str(manifest_row.get('authority') or '').strip()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\run_hmlr_inspire_low_disk.py:147: source_url = str(manifest_row.get('zip_url') or '')
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\run_hmlr_inspire_low_disk.py:194: str(record.get("inspire_id") or "").strip()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\run_hmlr_inspire_low_disk.py:196: if str(record.get("inspire_id") or "").strip()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\run_hmlr_inspire_low_disk.py:200: run = session.get(ETLRun, run_id)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\run_hmlr_inspire_low_disk.py:236: run = session.get(ETLRun, run_id)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\run_hmlr_inspire_low_disk.py:295: run = session.get(ETLRun, run_id)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\run_homes_england_backfill_loop.py:135: iterations = int(state.get("iterations", 0))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\run_homes_england_backfill_loop.py:137: "machine": os.environ.get("COMPUTERNAME") or socket.gethostname() or "unknown-machine",
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\run_homes_england_backfill_loop.py:142: held_by = f"{existing_lock.get('machine', 'unknown')}:{existing_lock.get('pid', 'unknown')}"
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\run_homes_england_backfill_loop.py:160: iterations = int(state.get("iterations", 0))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\run_homes_england_backfill_loop.py:179: iterations = int(state.get("iterations", 0))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\run_homes_england_backfill_loop.py:219: iterations = int(state.get("iterations", 0))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\run_homes_england_backfill_loop.py:273: iterations=int(state.get("iterations", 0)),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\run_homes_england_backfill_loop.py:312: iterations=int(state.get("iterations", 0)),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\run_homes_england_backfill_loop.py:318: f"({len(state.get('staged_offsets', []))}/{max(args.rebuild_every, 1)}).",
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\run_homes_england_backfill_loop.py:338: status = str(state.get("status") or "")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\run_homes_england_backfill_loop.py:339: authority = str(state.get("current_authority") or "").strip()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\run_homes_england_backfill_loop.py:340: current_offset = state.get("current_offset")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\run_local_brownfield_low_disk.py:39: active_entries = [row for row in load_manifest_records(adapter.manifest_path) if bool(row.get('is_active', True))]
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\run_local_brownfield_low_disk.py:42: next_index = int(state.get('next_index') or args.start_index)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\run_local_brownfield_low_disk.py:43: run_id = str(state.get('run_id') or '')
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\run_local_brownfield_low_disk.py:44: entries_completed = int(state.get('entries_completed') or 0)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\run_local_brownfield_low_disk.py:78: format_hint=(entry.get('format_hint') or '').strip().lower(),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\run_local_brownfield_low_disk.py:85: source_updated_at=parse_http_datetime(response.headers.get('Last-Modified')) or dt.datetime.now(dt.UTC),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\run_local_brownfield_low_disk.py:86: metadata={'mode': 'live', 'low_disk': True, 'manifest_index': index, 'local_authority': entry.get('local_authority')},
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\run_local_brownfield_low_disk.py:95: run = session.get(ETLRun, run_id)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\run_local_brownfield_low_disk.py:120: 'last_local_authority': entry.get('local_authority'),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\run_local_brownfield_low_disk.py:136: 'local_authority': entry.get('local_authority'),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\run_local_brownfield_low_disk.py:206: run = session.get(ETLRun, run_id)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\run_local_brownfield_low_disk.py:216: run = session.get(ETLRun, run_id)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\run_planning_brownfield_low_disk.py:38: next_url = str(state.get('next_url') or adapter._page_url(settings.planning_brownfield_url, offset=args.start_offset, limit=args.page_size))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\run_planning_brownfield_low_disk.py:39: run_id = str(state.get('run_id') or '')
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\run_planning_brownfield_low_disk.py:40: pages_completed = int(state.get('pages_completed') or 0)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\run_planning_brownfield_low_disk.py:69: response = http.get(
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\run_planning_brownfield_low_disk.py:76: features = payload.get('features', []) if isinstance(payload, dict) else []
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\run_planning_brownfield_low_disk.py:81: source_updated_at = source_updated_at or parse_http_datetime(response.headers.get('Last-Modified')) or dt.datetime.now(dt.UTC)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\run_planning_brownfield_low_disk.py:87: 'links': payload.get('links', {}) if isinstance(payload, dict) else {},
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\run_planning_brownfield_low_disk.py:106: source_updated_at=parse_http_datetime(response.headers.get('Last-Modified')) or dt.datetime.now(dt.UTC),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\run_planning_brownfield_low_disk.py:117: run = session.get(ETLRun, run_id)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\run_planning_brownfield_low_disk.py:232: run = session.get(ETLRun, run_id)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\run_planning_brownfield_low_disk.py:242: run = session.get(ETLRun, run_id)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\run_planning_brownfield_low_disk.py:254: run = session.get(ETLRun, run_id)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\safe_public_site_geometry_probe.py:115: if tag.lower() == "a" and attr.get("href"):
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\safe_public_site_geometry_probe.py:118: if tag.lower() == "img" and (attr.get("src") or attr.get("data-src")):
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\safe_public_site_geometry_probe.py:119: src = attr.get("src") or attr.get("data-src") or ""
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\safe_public_site_geometry_probe.py:120: alt = " ".join([_clean(attr.get("alt")), _clean(attr.get("title")), _clean(attr.get("aria-label"))]).strip()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\safe_public_site_geometry_probe.py:123: if attr.get(k):
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\safe_public_site_geometry_probe.py:152: return {"url": meta.get("resolved_url", url), "status": meta.get("status", 0), "content_type": meta.get("content_type", ""), "text": cache_path.read_text(encoding="utf-8", errors="ignore"), "from_cache": True, "error": ""}
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\safe_public_site_geometry_probe.py:156: r = requests.get(url, headers={"User-Agent": UA, "Accept": "text/html,application/xhtml+xml,*/*"}, timeout=timeout_s, allow_redirects=True)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\safe_public_site_geometry_probe.py:157: ctype = r.headers.get("content-type", "")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\safe_public_site_geometry_probe.py:230: typ = gj.get("type")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\safe_public_site_geometry_probe.py:231: coords = gj.get("coordinates")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\safe_public_site_geometry_probe.py:282: for cand in ev.get("geojson_candidates", []):
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\safe_public_site_geometry_probe.py:283: if cand.get("accepted") and cand.get("geojson"):
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sold_buildings_handoff.py:164: records = payload.get("records")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sold_buildings_handoff.py:216: writer.writerow({key: row.get(key) for key in fieldnames})
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sold_buildings_handoff.py:280: parcel = session.get(ParcelInspire, int(parcel_id))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sold_buildings_handoff.py:406: target_count = int(state_payload.get("target_count", 0) or 0)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sold_buildings_handoff.py:407: last_parcel_id = int(state_payload.get("last_parcel_id", 0) or 0)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sold_buildings_handoff.py:672: parcel_info = parcel_by_id.get(parcel_id)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sold_buildings_handoff.py:680: metadata.get("building_area_m2")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sold_buildings_handoff.py:684: parcel_area_m2 = _safe_float(parcel_info.get("area_m2"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sold_buildings_handoff.py:692: metadata.get("price_per_m2_gbp")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sold_buildings_handoff.py:698: str(metadata.get("location_label")).strip()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sold_buildings_handoff.py:699: if isinstance(metadata, dict) and metadata.get("location_label") not in (None, "")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sold_buildings_handoff.py:701: ) or txn.town_city or txn.county or parcel_info.get("local_authority")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\split_market_batch_by_match_hints.py:9: return bool((row.get("matched_parcel_ref") or "").strip() or (row.get("matched_inspire_id") or "").strip())
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\strict_sales_geometry_confidence_ranker.py:73: lid = clean(item.get("listing_id"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\strict_sales_geometry_confidence_ranker.py:74: ev = item.get("evidence", {})
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\strict_sales_geometry_confidence_ranker.py:87: lid = clean(r.get("listing_id"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\strict_sales_geometry_confidence_ranker.py:95: lid = clean(r.get("listing_id"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\strict_sales_geometry_confidence_ranker.py:103: lid = clean(r.get("listing_id"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\strict_sales_geometry_confidence_ranker.py:112: src = clean(row.get("area_source")).lower()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\strict_sales_geometry_confidence_ranker.py:113: raw = clean(row.get("area_raw")).lower()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\strict_sales_geometry_confidence_ranker.py:123: src = clean(row.get("area_source")).lower()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\strict_sales_geometry_confidence_ranker.py:124: raw = clean(row.get("area_raw")).lower()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\strict_sales_geometry_confidence_ranker.py:129: src = clean(row.get("area_source")).lower()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\strict_sales_geometry_confidence_ranker.py:130: raw = clean(row.get("area_raw")).lower()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\strict_sales_geometry_confidence_ranker.py:135: ev = aux["evidence"].get(lid, {})
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\suggest_market_batch_matches.py:15: r"C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\data\live_feeds\drops\market\repo_manual_match_batch_immediate.csv"
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\suggest_market_batch_matches.py:18: r"C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\data\live_feeds\drops\market\repo_manual_match_batch_immediate_suggestions.csv"
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\suggest_market_batch_matches.py:198: exact = exact_lookup.get(raw.lower())
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\suggest_market_batch_matches.py:205: candidates = norm_lookup.get(normalized) or []
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\suggest_market_batch_matches.py:276: title_numbers = _clean(row.get("title_numbers"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\suggest_market_batch_matches.py:279: local_authority = _clean(row.get("_resolved_local_authority") or row.get("local_authority"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\suggest_market_batch_matches.py:303: footprint_geojson = _json_text_or_none(row.get("sale_footprint_geojson")) or _json_text_or_none(row.get("geometry_geojson"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\suggest_market_batch_matches.py:307: site_area = _float_or_none(row.get("site_area_m2"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\suggest_market_batch_matches.py:308: local_authority = _clean(row.get("_resolved_local_authority") or row.get("local_authority"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\suggest_market_batch_matches.py:362: latitude = _float_or_none(row.get("latitude"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\suggest_market_batch_matches.py:363: longitude = _float_or_none(row.get("longitude"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\suggest_market_batch_matches.py:366: site_area = _float_or_none(row.get("site_area_m2"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\targeted_low_tier_visual_confidence_upgrade.py:25: r=requests.get(url,headers={'User-Agent':'Mozilla/5.0 targeted-sale-geometry-confidence/1.0'},timeout=35); r.raise_for_status(); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(r.text,encoding='utf-8',errors='ignore'); return r.text,'network'
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\targeted_low_tier_visual_confidence_upgrade.py:50: r=requests.get(u,headers={'User-Agent':'Mozilla/5.0 targeted-sale-geometry-confidence/1.0'},stream=True,timeout=45); r.raise_for_status(); total=int(r.headers.get('content-length') or 0)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\targeted_low_tier_visual_confidence_upgrade.py:80: blob=' '.join([page or '',' '.join(links),' '.join(s(d.get('url')) for d in dls),s(row.get('verification_note')),s(row.get('area_hits'))])
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\targeted_low_tier_visual_confidence_upgrade.py:81: ah=areas(blob); src_area=bool(ah) or s(row.get('source_area')).lower()=='yes' or bool(s(row.get('estimated_area_m2')))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\targeted_low_tier_visual_confidence_upgrade.py:82: plan=bool(PLAN.search(blob)); ref=bool(REF.search(blob)); poly=bool(POLY.search(blob)); high=[u for u in links if lscore(u)>=45]; doc=bool([d for d in dls if s(d.get('path'))]) or bool(high)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\targeted_low_tier_visual_confidence_upgrade.py:85: p=Path(s(d.get('path')))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\targeted_low_tier_visual_confidence_upgrade.py:88: ot=s(row.get('confidence_tier')); os=n(row.get('confidence_score'))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\targeted_low_tier_visual_confidence_upgrade.py:95: else: nt,ns,lab=ot,os,s(row.get('confidence_label'))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\targeted_low_tier_visual_confidence_upgrade.py:96: if ns<os: nt,ns,lab=ot,os,s(row.get('confidence_label'))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\targeted_low_tier_visual_confidence_upgrade.py:97: note=f"TARGETED_LOW_TIER_UPGRADE | old={ot}/{os} | new={nt}/{ns} | source_area={'yes' if src_area else 'no'} | plan_signal={'yes' if plan else 'no'} | visual_boundary={'yes' if visual else 'no'} | public_doc={'yes' if doc else 'no'} | reference={'yes' if ref else 'no'} | polygon_signal={'yes' if poly else 'no'} | area_hits={'; '.join(ah[:10])} | high_value_links={len(high)} | downloads={len([d for d in dls if s(d.get('path'))])} | visual_pixels={pixels} | Official parcel system is not proof."
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\targeted_low_tier_visual_confidence_upgrade.py:98: return {'listing_id':s(row.get('listing_id')),'listing_url':s(row.get('listing_url')),'old_confidence_tier':ot,'old_confidence_score':os,'new_confidence_tier':nt,'new_confidence_score':ns,'new_confidence_label':lab,'upgraded':'yes' if ns>os else 'no','source_area':'yes' if src_area else 'no','plan_signal':'yes' if plan else 'no','visual_boundary_signal':'yes' if visual else 'no','public_doc_downloaded':'yes' if doc else 'no','reference_signal':'yes' if ref else 'no','polygon_signal':'yes' if poly else 'no','area_hits':'; '.join(ah[:10]),'downloaded_count':len([d for d in dls if s(d.get('path'))]),'downloaded_bytes':sum(int(d.get('bytes') or 0) for d in dls if s(d.get('path'))),'visual_boundary_pixels':pixels,'verification_note':note}
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\targeted_low_tier_visual_confidence_upgrade.py:115: lid=s(row.get('listing_id')); url=s(row.get('listing_url')); print(f'[{i}/{len(rows)}] {lid} {row.get("confidence_tier")} {url}',flush=True)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\upgrade_candidate_confidence_and_lengths.py:64: old = clean(row.get("confidence_level"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\upgrade_candidate_confidence_and_lengths.py:65: method = clean(row.get("generation_method"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\upgrade_candidate_confidence_and_lengths.py:66: area_source = clean(row.get("area_source"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\upgrade_candidate_confidence_and_lengths.py:67: docs = clean(row.get("doc_evidence_available")).lower() == "yes"
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\upgrade_candidate_confidence_and_lengths.py:68: planning = bool(clean(row.get("planning_refs")))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\upgrade_candidate_confidence_and_lengths.py:69: lot = bool(clean(row.get("lot_refs")))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\upgrade_candidate_confidence_and_lengths.py:70: title = bool(clean(row.get("title_refs")))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\upgrade_candidate_confidence_and_lengths.py:112: old_conf = clean(r.get("confidence_level"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\upgrade_candidate_confidence_and_lengths.py:113: summary["old_confidence_counts"][old_conf] = summary["old_confidence_counts"].get(old_conf, 0) + 1
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\upgrade_candidate_confidence_and_lengths.py:116: summary["new_confidence_counts"][new_conf] = summary["new_confidence_counts"].get(new_conf, 0) + 1
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\upgrade_candidate_confidence_and_lengths.py:122: sides = parse_sides(clean(r.get("side_lengths_m_json")))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\upgrade_candidate_confidence_and_lengths.py:124: area = fmt_m2(r.get("estimated_area_m2"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\upgrade_d_tier_sale_geometry_confidence.py:26: r=requests.get(url,headers={'User-Agent':'Mozilla/5.0 sale-geometry-d-tier-evidence/1.0','Accept':'text/html,*/*'},timeout=30)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\upgrade_d_tier_sale_geometry_confidence.py:64: r=requests.get(url,headers={'User-Agent':'Mozilla/5.0 sale-geometry-d-tier-evidence/1.0'},stream=True,timeout=35); r.raise_for_status()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\upgrade_d_tier_sale_geometry_confidence.py:65: total=int(r.headers.get('content-length') or 0)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\upgrade_d_tier_sale_geometry_confidence.py:87: dl=[d['url'] for d in downs if d.get('path')]
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\upgrade_d_tier_sale_geometry_confidence.py:88: blob=' '.join([page or '', ' '.join(all_links), ' '.join(dl+[d.get('path','') for d in downs]), clean(row.get('verification_note')), clean(row.get('area_hits')), clean(row.get('confidence_label'))])
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\upgrade_d_tier_sale_geometry_confidence.py:90: source_area=bool(hits) or clean(row.get('source_area')).lower()=='yes' or bool(clean(row.get('estimated_area_m2')))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\upgrade_d_tier_sale_geometry_confidence.py:102: return {'new_confidence_tier':tier,'new_confidence_score':score,'new_confidence_label':label,'source_area':'yes' if source_area else 'no','plan_signal':'yes' if plan else 'no','public_doc_downloaded':'yes' if doc else 'no','reference_signal':'yes' if ref else 'no','polygon_signal':'yes' if poly else 'no','area_hits':'; '.join(hits[:10]),'all_links_found':len(all_links),'high_value_links_found':len(high),'downloaded_count':len(dl),'downloaded_bytes':sum(int(d.get('bytes') or 0) for d in downs if d.get('path')),'downloaded_urls':' | '.join(dl[:30]),'top_evidence_links':' | '.join(high[:30])}
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\upgrade_d_tier_sale_geometry_confidence.py:129: trs.append(f"<tr><td><b>{clean(r.get('listing_id'))}</b><br><a target='_blank' href='{clean(r.get('listing_url'))}'>listing</a></td><td>{clean(r.get('old_confidence_tier'))} â†’ <b>{clean(r.get('new_confidence_tier'))}</b><br>{clean(r.get('new_confidence_score'))}/100<br>{clean(r.get('new_confidence_label'))}</td><td>area={clean(r.get('source_area'))}<br>plan={clean(r.get('plan_signal'))}<br>doc={clean(r.get('public_doc_downloaded'))}<br>ref={clean(r.get('reference_signal'))}<br>polygon={clean(r.get('polygon_signal'))}</td><td>links={clean(r.get('all_links_found'))}<br>evidence={clean(r.get('high_value_links_found'))}<br>downloads={clean(r.get('downloaded_count'))}<br>MB={round(int(r.get('downloaded_bytes') or 0)/1024/1024,2)}</td><td>{clean(r.get('verification_note'))[:700]}</td></tr>")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\upgrade_d_tier_sale_geometry_confidence.py:138: lid=clean(row.get('listing_id')); url=clean(row.get('listing_url')); print(f'[{i}/{len(rows)}] {lid} {url}',flush=True)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\upgrade_d_tier_sale_geometry_confidence.py:144: cls=classify(row,page,all_links,downs); old_score=as_int(row.get('confidence_score')); old_tier=clean(row.get('confidence_tier')); new_score=as_int(cls['new_confidence_score']); upgraded=new_score>old_score
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\upgrade_d_tier_sale_geometry_confidence.py:146: out={'listing_id':lid,'listing_url':url,'old_confidence_tier':old_tier,'old_confidence_score':old_score,'upgraded':'yes' if upgraded else 'no','confidence_tier':cls['new_confidence_tier'] if upgraded else old_tier,'confidence_score':new_score if upgraded else old_score,'confidence_label':cls['new_confidence_label'] if upgraded else clean(row.get('confidence_label')),'source_level':'d_tier_deep_media_upgrade' if upgraded else clean(row.get('source_level')),'verification_note':note,'fetch_status':status,'top_selected_links':' | '.join(selected[:30]),**cls}
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\upgrade_d_tier_sale_geometry_confidence.py:151: counts[r['confidence_tier']]=counts.get(r['confidence_tier'],0)+1
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\validate_live_listing_manifests.py:11: active = status.get("active_entries", 0)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\validate_live_listing_manifests.py:12: live_ready = status.get("live_ready_entries", 0)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\validate_live_listing_manifests.py:13: demo = status.get("demo_entries", 0)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\validate_live_listing_manifests.py:14: availability = status.get("availability", "unknown")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\validate_live_listing_manifests.py:20: print(f"  manifest_path: {status.get('manifest_path')}")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\validate_live_listing_manifests.py:21: active_provider_names = status.get("active_provider_names") or []
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\validate_live_listing_manifests.py:24: missing_active_files = [item for item in (status.get("missing_active_files") or []) if item]
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\validate_live_listing_manifests.py:27: if status.get("parse_error"):
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\validate_live_listing_manifests.py:53: if status.get("has_live_ready_manifest")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\validate_live_listing_manifests.py:61: print("next_step: put a real export file into data/live_feeds/drops/... and set active=true in the matching manifest")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\match\parcel_matcher.py:168: return authority_lookup.get(canonical)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\match\parcel_matcher.py:370: hints = metadata.get('match_hints')
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\match\parcel_matcher.py:377: matched_inspire_id = str(hints.get('matched_inspire_id') or '').strip()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\match\parcel_matcher.py:378: matched_parcel_ref = str(hints.get('matched_parcel_ref') or '').strip()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\match\parcel_matcher.py:549: parcel_id = row.get('parcel_id')
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\match\parcel_matcher.py:556: bridge_conf = float(row.get('confidence_score') or 0.0)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\match\parcel_matcher.py:557: bridge_match = float(row.get('match_score') or 0.0)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\match\parcel_matcher.py:643: parcel_id_raw = row.get('parcel_id')
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\match\parcel_matcher.py:648: bridge_conf = float(row.get('confidence_score') or 0.0)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\match\parcel_matcher.py:649: bridge_match = float(row.get('match_score') or 0.0)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\match\parcel_matcher.py:655: row.get('listing_address'),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\match\parcel_matcher.py:656: row.get('listing_title'),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\publish\parcel_signal_summary.py:180: item.get("source_updated_at") or "",
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\publish\parcel_signal_summary.py:181: float(item.get("confidence_score") or 0),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\publish\parcel_signal_summary.py:234: source_ids = source_ids_by_name.get(source_name)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\publish\parcel_signal_summary.py:248: parcel_links = grouped_links.get(parcel.parcel_id, [])
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\publish\parcel_signal_summary.py:273: records_for_source = [source_records.get(source_name, {}).get(link.source_record_id) for link in links_for_source]
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\publish\parcel_signal_summary.py:308: visible_sale_records = [item for item in active_sale_records if item.get("source_tier") != "demo" and not item.get("is_demo")]
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\publish\parcel_signal_summary.py:312: top_actionable_truth = top_actionable_listing.get("price_truth") if isinstance(top_actionable_listing, dict) else {}
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\publish\parcel_signal_summary.py:314: demo_sale_count = sum(1 for item in active_sale_records if item.get("source_tier") == "demo" or item.get("is_demo"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\publish\parcel_signal_summary.py:315: official_sale_visible_count = sum(1 for item in active_sale_records if item.get("source_tier") == "official")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\publish\parcel_signal_summary.py:316: licensed_sale_visible_count = sum(1 for item in active_sale_records if item.get("source_tier") == "licensed")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\publish\parcel_signal_summary.py:317: manual_sale_visible_count = sum(1 for item in active_sale_records if item.get("source_tier") == "manual")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\publish\parcel_signal_summary.py:321: if isinstance(item.get("price_truth"), dict) and item["price_truth"].get("is_real") is True and _to_number(item.get("ask_price")) not in (None, 0)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\common.py:15: from shapely.ops import transform as shapely_transform
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\common.py:22: if isinstance(payload, dict) and isinstance(payload.get('records'), list):
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\common.py:24: if isinstance(payload, dict) and isinstance(payload.get('features'), list):
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\common.py:147: for ring in geometry.get('rings', []):
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\government_property_finder.py:38: manifest = row.get("__manifest_entry") or {}
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\government_property_finder.py:39: field_mapping = manifest.get("field_mapping") or {}
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\government_property_finder.py:40: status_mapping = manifest.get("status_mapping") or {}
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\government_property_finder.py:55: source_srid=int(manifest.get("source_srid", 4326)),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\government_property_finder.py:65: source_srid=int(manifest.get("source_srid", 4326)),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\government_property_finder.py:72: truth_tier=manifest.get("truth_tier") or "official",
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\government_property_finder.py:73: is_demo=manifest.get("is_demo"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\government_property_finder.py:80: "provider_name": manifest.get("provider_name") or "Government Property Finder",
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\government_property_finder.py:81: "provider_kind": manifest.get("provider_kind") or "official_export",
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\government_property_finder.py:83: "license_scope": manifest.get("license_scope") or "government_export",
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\government_property_finder.py:85: "is_demo": bool(manifest.get("is_demo")) or truth_tier == "demo",
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\government_property_finder.py:95: "source_url": row.get("__source_url"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\hmlr_inspire.py:37: if str(row.get('country') or '').strip().lower() == 'england'
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\hmlr_inspire.py:47: zip_name = str(record.get('zip_name') or Path(str(record.get('zip_url') or '')).name)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\hmlr_inspire.py:56: 'authority': record.get('authority'),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\hmlr_inspire.py:57: 'zip_url': record.get('zip_url'),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\hmlr_inspire.py:60: 'country': record.get('country'),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\hmlr_inspire.py:79: zip_name = str(manifest_row.get('zip_name') or Path(str(manifest_row.get('zip_url') or '')).name)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\hmlr_inspire.py:116: listing_response = session.get(listing_url, timeout=self.settings.http_timeout_s)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\hmlr_inspire.py:122: response = session.get(zip_url, timeout=self.settings.http_timeout_s)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\hmlr_inspire.py:130: content_type = response.headers.get('content-type') or response.headers.get('Content-Type') or ''
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\hmlr_inspire.py:155: if extract.metadata.get('mode') != 'live':
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\hmlr_inspire.py:159: manifest_rows = payload.get('records', [])
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\hmlr_inspire.py:164: zip_path = Path(str(manifest_row.get('zip_local_path') or '')).expanduser()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\hmlr_price_paid.py:28: source_updated_at=parse_http_datetime(response.headers.get('Last-Modified')) or dt.datetime.now(dt.UTC),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\homes_england_landhub.py:24: response = session.get(
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\homes_england_landhub.py:39: if payload.get('error'):
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\homes_england_landhub.py:43: source_updated_at = source_updated_at or parse_http_datetime(response.headers.get('Last-Modified'))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\homes_england_landhub.py:44: features = payload.get('features') or []
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\homes_england_landhub.py:49: exceeded = bool(payload.get('exceededTransferLimit'))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\homes_england_landhub.py:87: if row.get('listing_id'):
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\homes_england_landhub.py:88: normalized.append({**row, 'marketing_status': self._normalize_status(row.get('marketing_status'))})
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\homes_england_landhub.py:91: attrs = row.get('attributes', row)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\homes_england_landhub.py:170: 'geometry_wkt': arcgis_geometry_to_wkt(row.get('geometry')),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\homes_england_landhub.py:171: 'source_url': row.get('__source_url') or self.settings.homes_england_url,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\homes_england_landhub.py:174: or parse_datetime_like(row.get('__source_updated_at'))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\http_client.py:50: response = session.get(
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\local_authority_brownfield.py:24: active_entries = [row for row in manifest if bool(row.get('is_active', True))]
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\local_authority_brownfield.py:35: last_updated = last_updated or parse_http_datetime(response.headers.get('Last-Modified'))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\local_authority_brownfield.py:36: format_hint = (entry.get('format_hint') or '').strip().lower()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\local_authority_brownfield.py:59: if row.get('site_id'):
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\local_authority_brownfield.py:63: manifest_entry = row.get('__manifest_entry', {})
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\local_authority_brownfield.py:64: props = row.get('properties', row)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\local_authority_brownfield.py:67: props,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\local_authority_brownfield.py:73: default=f"{manifest_entry.get('local_authority', 'la')}-{len(normalized)+1}",
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\local_authority_brownfield.py:77: geometry = row.get('geometry')
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\local_authority_brownfield.py:81: if geometry.get('type') == 'Point':
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\local_authority_brownfield.py:86: geo_x = pick_first(props, 'GeoX', 'geo_x', 'x')
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\local_authority_brownfield.py:87: geo_y = pick_first(props, 'GeoY', 'geo_y', 'y')
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\manual_listing_exports.py:17: if isinstance(payload, dict) and isinstance(payload.get(container_key), list):
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\manual_listing_exports.py:40: if active_only and not bool(entry.get("active", True)):
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\manual_listing_exports.py:42: export_path = resolve_manifest_file(manifest_path, entry.get("file_drop_path"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\manual_listing_exports.py:44: missing_files.append(str(entry.get("file_drop_path") or ""))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\manual_listing_exports.py:46: input_format = str(entry.get("input_format") or export_path.suffix.lstrip(".") or "json").lower()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\manual_listing_exports.py:53: source_updated_at = entry.get("source_updated_at") or dt.datetime.fromtimestamp(export_path.stat().st_mtime, tz=dt.UTC).isoformat()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\manual_listing_exports.py:78: mapped = mapping.get(canonical_name)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\planning_data_brownfield.py:27: response = session.get(
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\planning_data_brownfield.py:35: source_updated_at = source_updated_at or parse_http_datetime(response.headers.get('Last-Modified'))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\planning_data_brownfield.py:36: all_features.extend(payload.get('features', []) if isinstance(payload, dict) else [])
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\planning_data_brownfield.py:53: source_updated_at=parse_http_datetime(response.headers.get('Last-Modified')) or dt.datetime.now(dt.UTC),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\planning_data_brownfield.py:85: if row.get('site_id'):
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\planning_data_brownfield.py:89: props = row.get('properties', row)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\planning_data_brownfield.py:90: entity = pick_first(props, 'entity', 'reference', 'site-reference')
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\planning_data_brownfield.py:92: geometry = row.get('geometry')
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\planning_data_brownfield.py:96: if geometry.get('type') == 'Point':
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\planning_data_brownfield.py:101: point_wkt = point_wkt or transform_wkt(pick_first(props, 'point', 'Point'), source_srid=4326, target_srid=27700)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\planning_data_brownfield.py:102: geometry_wkt = geometry_wkt or transform_wkt(pick_first(props, 'geometry', 'site-geometry'), source_srid=4326, target_srid=27700, force_multipolygon=True)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\planning_data_brownfield.py:103: entry_date = parse_datetime_like(pick_first(props, 'entry-date', 'entry_date', 'entryDate'))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\facilities\base.py:64: if isinstance(payload, dict) and isinstance(payload.get("records"), list):
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\facilities\base.py:66: if isinstance(payload, dict) and isinstance(payload.get("features"), list):
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\facilities\base.py:76: explicit_mode = str(entry.get("mode") or "").strip().lower()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\facilities\base.py:79: if entry.get("download_url") or entry.get("download_urls"):
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\facilities\base.py:86: primary = entry.get("download_url")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\facilities\base.py:89: extra_urls = entry.get("download_urls")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\facilities\base.py:116: configured = str(entry.get("input_format") or "").strip().lower()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\facilities\base.py:135: return [], "", entry.get("source_updated_at")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\facilities\base.py:138: parse_http_datetime(response.headers.get("Last-Modified")) or parse_http_datetime(entry.get("source_updated_at"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\facilities\base.py:154: return rows, resolved_url, source_updated_at.isoformat() if source_updated_at else entry.get("source_updated_at")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\facilities\base.py:157: configured = entry.get("source_updated_at")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\facilities\base.py:167: props = self._extract_properties(row)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\market\vendor_feed.py:33: "provider_count": len({(row.get("__manifest_entry") or {}).get("provider_name") for row in records}),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\market\vendor_feed.py:48: manifest = row.get("__manifest_entry") or {}
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\market\vendor_feed.py:49: field_mapping = manifest.get("field_mapping") or {}
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\market\vendor_feed.py:50: status_mapping = manifest.get("status_mapping") or {}
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\market\vendor_feed.py:51: provider_name = str(manifest.get("provider_name") or row.get("provider_name") or self.provider_name()).strip()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\market\vendor_feed.py:52: provider_kind = str(manifest.get("provider_kind") or "licensed_vendor").strip() or "licensed_vendor"
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\market\vendor_feed.py:58: truth_tier=manifest.get("truth_tier"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\market\vendor_feed.py:59: is_demo=manifest.get("is_demo"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\market\vendor_feed.py:83: source_srid=int(manifest.get("source_srid", 4326)),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\market\vendor_feed.py:93: source_srid=int(manifest.get("source_srid", 4326)),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\market\vendor_feed.py:117: "license_scope": manifest.get("license_scope") or "licensed_export",
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\market\vendor_feed.py:119: "is_demo": bool(manifest.get("is_demo")) or truth_tier == "demo",
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\planned\generic_official_pdf.py:38: text = str(row.get("text") or row.get("content") or "")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\planned\generic_official_pdf.py:39: title = str(row.get("title") or f"Official PDF Project {idx}").strip()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\planned\generic_official_pdf.py:40: source_url = str(row.get("source_url") or row.get("url") or "").strip()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\planned\generic_official_pdf.py:57: planning_reference = row.get("planning_reference")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\planned\generic_official_pdf.py:59: planning_reference = row.get("reference")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\planned\generic_official_pdf.py:74: "source_record_id": str(row.get("record_id") or f"pdf-{idx}"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\planned\generic_official_pdf.py:75: "source_id": str(row.get("source_id") or "generic_official_pdf"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\planned\generic_official_pdf.py:76: "source_name": str(row.get("source_name") or "Official Council PDF"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\planned\generic_official_pdf.py:77: "source_type": str(row.get("source_type") or "official_council_pdf"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\planned\generic_official_pdf.py:79: "asset_type": str(row.get("asset_type") or "regeneration_area"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\planned\generic_official_pdf.py:80: "asset_subtype": row.get("asset_subtype"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\planned\generic_official_pdf.py:84: "local_authority": row.get("local_authority"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\planned\planning_data_gov_uk.py:27: response = session.get(
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\planned\planning_data_gov_uk.py:35: source_updated_at = source_updated_at or parse_http_datetime(response.headers.get("Last-Modified"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\planned\planning_data_gov_uk.py:36: all_features.extend(payload.get("features", []) if isinstance(payload, dict) else [])
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\planned\planning_data_gov_uk.py:51: source_updated_at=parse_http_datetime(response.headers.get("Last-Modified")) or dt.datetime.now(dt.UTC),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\planned\planning_data_gov_uk.py:80: props = row.get("properties", row)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\planned\planning_data_gov_uk.py:81: entity = pick_first(props, "entity", "reference", "site-reference")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\planned\planning_data_gov_uk.py:82: source_record_id = str(entity or pick_first(props, "site_id", "site-reference", default="unknown"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\planned\planning_data_gov_uk.py:85: props,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\planned\planning_data_gov_uk.py:92: geometry_wkt = geometry_to_wkt(row.get("geometry"), source_srid=4326, target_srid=27700, force_multipolygon=True)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\planned\planning_data_gov_uk.py:94: if isinstance(row.get("geometry"), dict) and row["geometry"].get("type") == "Point":
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\planned\planning_data_gov_uk.py:95: coords = row["geometry"].get("coordinates") or []
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\planned\planning_data_gov_uk.py:99: entry_date = parse_datetime_like(pick_first(props, "entry-date", "entry_date", "entryDate"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\city_vector_service.py:90: city_name = str(row.get("city_name") or "Unknown")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\city_vector_service.py:91: parcel_count = int(row.get("parcel_count") or 0)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\city_vector_service.py:92: base_lon = float(row.get("base_lon") or 0.0)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\city_vector_service.py:93: base_lat = float(row.get("base_lat") or 0.0)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\city_vector_service.py:94: weight_sum = float(row.get("weight_sum") or 0.0)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\city_vector_service.py:95: avg_confidence = float(row.get("avg_confidence") or 0.0)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\city_vector_service.py:96: avg_growth = float(row.get("avg_growth") or 0.0)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\city_vector_service.py:104: weighted_lon = float(row.get("weighted_lon_sum") or 0.0) / weight_sum
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\city_vector_service.py:105: weighted_lat = float(row.get("weighted_lat_sum") or 0.0) / weight_sum
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\config.py:32: source_key=str(raw.get("source_key") or "").strip(),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\config.py:33: source_name=str(raw.get("source_name") or "").strip(),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\config.py:34: publisher=str(raw.get("publisher") or "").strip(),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\config.py:35: source_type=str(raw.get("source_type") or "").strip(),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\config.py:36: source_url=str(raw.get("source_url") or "").strip(),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\config.py:37: licence=str(raw.get("licence") or "").strip(),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\config.py:38: update_frequency=str(raw.get("update_frequency") or "").strip(),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\config.py:39: purpose=str(raw.get("purpose") or "").strip(),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\config.py:40: geography=str(raw.get("geography") or "").strip(),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\config.py:41: connector=str(raw.get("connector") or "").strip(),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\config.py:42: default_mode=str(raw.get("default_mode") or "fixture").strip().lower(),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\config.py:43: fixture_path=str(raw.get("fixture_path")).strip() if raw.get("fixture_path") else None,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\evidence_service.py:105: relation_type = str(data.get("relation_type") or "")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\evidence_service.py:106: geography_level = str(data.get("geography_level") or "")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\evidence_service.py:110: data["relation_label"] = RELATION_TYPE_LABELS.get(relation_type, relation_type)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\evidence_service.py:120: if any(row.get("display_warning") for row in evidence_rows):
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\evidence_service.py:129: "local_authority_code": score.get("local_authority_code"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\evidence_service.py:145: "city_growth_direction_label": score.get("city_growth_direction_label") or "insufficient evidence",
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\evidence_service.py:159: factor = str(row.get("factor_type") or "unknown")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\evidence_service.py:160: impact = float(row.get("impact_weight") or 0.0)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\evidence_service.py:166: sample = sample_by_factor.get(factor, {})
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\evidence_service.py:171: "sample_evidence_title": sample.get("evidence_title"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\evidence_service.py:172: "sample_source_title": sample.get("source_title"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\evidence_service.py:173: "sample_relation_type": sample.get("relation_type"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\ingestion_service.py:137: external_id = self._fit_external_id(str(row.get("external_id") or ""), external_id_max_len)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\ingestion_service.py:141: feature_type=str(row.get("feature_type") or "unknown"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\ingestion_service.py:143: name=row.get("name"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\ingestion_service.py:144: description=row.get("description"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\ingestion_service.py:145: geometry=wkt_to_element(row.get("geometry"), srid=27700),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\ingestion_service.py:146: centroid=wkt_to_element(row.get("centroid"), srid=27700),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\ingestion_service.py:147: geography_level=row.get("geography_level"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\ingestion_service.py:148: local_authority_code=self._fit_optional_token(row.get("local_authority_code"), local_authority_max_len),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\ingestion_service.py:149: lsoa_code=self._fit_optional_token(row.get("lsoa_code"), lsoa_max_len),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\ingestion_service.py:150: msoa_code=self._fit_optional_token(row.get("msoa_code"), msoa_max_len),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\ingestion_service.py:151: valid_from=row.get("valid_from"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\ingestion_service.py:152: valid_to=row.get("valid_to"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\scoring_service.py:92: city_growth_direction_label=vector_labels.get(str(parcel.get("local_authority") or "").lower()),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\scoring_service.py:105: feature_id=int(evidence["feature_id"]) if evidence.get("feature_id") is not None else None,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\scoring_service.py:108: source_title=evidence.get("source_title"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\scoring_service.py:109: source_url=evidence.get("source_url"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\scoring_service.py:110: source_publisher=evidence.get("source_publisher"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\scoring_service.py:111: publication_date=evidence.get("publication_date"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\scoring_service.py:112: data_date=evidence.get("data_date"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\scoring_service.py:113: geography_level=evidence.get("geography_level"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\scoring_service.py:115: distance_m=evidence.get("distance_m"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\scoring_service.py:117: extracted_claim=evidence.get("extracted_claim"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\scoring_service.py:118: confidence=evidence.get("confidence"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\scoring_service.py:119: raw_json=evidence.get("raw_json") or {},
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\scoring_utils.py:80: return GEOGRAPHY_CONFIDENCE_CAP.get(normalized, 60.0)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\scoring_utils.py:98: source_key = str(row.get("source_key") or "").strip().lower()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\scoring_utils.py:99: reliability_values.append(SOURCE_RELIABILITY.get(source_key, 0.62))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\scoring_utils.py:100: data_date = row.get("data_date")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\scoring_utils.py:101: pub_date = row.get("publication_date")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\scoring_utils.py:103: relation_type = str(row.get("relation_type") or "SAME_LOCAL_AUTHORITY").strip().upper()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\scoring_utils.py:104: relation_values.append(RELATION_TYPE_WEIGHT.get(relation_type, 0.2))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\scoring_utils.py:105: caps.append(_geography_cap(row.get("geography_level")))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\scoring_utils.py:106: if row.get("source_key"):
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\scoring_utils.py:107: independent_sources.add(str(row.get("source_key")))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\scoring_utils.py:108: if not row.get("source_url"):
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\scoring_utils.py:110: impact = float(row.get("impact_weight") or 0.0)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\tile_service.py:116: geometry = json.loads(row["geometry_json"]) if row.get("geometry_json") else None
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\tile_service.py:173: "local_authority_code": row.get("local_authority_code"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\tile_service.py:174: "city_name": row.get("city_name"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\tile_service.py:175: "base_centroid": json.loads(row["base_centroid_json"]) if row.get("base_centroid_json") else None,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\tile_service.py:176: "weighted_future_centroid": json.loads(row["weighted_future_centroid_json"]) if row.get("weighted_future_centroid_json") else None,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\tile_service.py:177: "vector_geometry": json.loads(row["vector_geometry_json"]) if row.get("vector_geometry_json") else None,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\tile_service.py:178: "direction_label": row.get("direction_label"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\tile_service.py:179: "strength_score": float(row.get("strength_score") or 0.0),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\tile_service.py:180: "confidence_score": float(row.get("confidence_score") or 0.0),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\tile_service.py:181: "horizon_years": int(row.get("horizon_years") or 5),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\tile_service.py:182: "calculation_version": row.get("calculation_version"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\tile_service.py:183: "calculated_at": row.get("calculated_at"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\middleware\map_listings_cache.py:22: cached = self.cache.get(key)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\middleware\map_listings_cache.py:33: content_type = str(response.headers.get("content-type") or "").lower()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\middleware\map_listings_cache.py:39: media_type = response.media_type or headers.get("content-type", "application/json")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\schemas\contractor.py:8: class ContractorExportRowsResponse(BaseModel):
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\schemas\contractor.py:16: class ContractorStatusResponse(BaseModel):
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\schemas\contractor.py:28: class ContractorParcelContactsResponse(BaseModel):
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\schemas\contractor.py:31: source_contractors_file: str
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\schemas\cost.py:92: contractor_ohp: float
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\schemas\ops.py:18: contractor_preflight_path: str
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\admin_service.py:36: return payload.get("regions", [])
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\admin_service.py:43: bbox = region.get("bbox") or []
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\admin_service.py:48: return region.get("slug")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\admin_service.py:87: if not manifest_status.get("manifest_exists"):
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\admin_service.py:95: if manifest_status.get("parse_error"):
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\admin_service.py:102: missing_files = [item for item in manifest_status.get("missing_active_files", []) if item]
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\admin_service.py:110: has_demo_only_manifest = bool(manifest_status.get("has_demo_only_manifest"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\admin_service.py:118: availability = manifest_status.get("availability")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\admin_service.py:126: elif row_count == 0 and not manifest_status.get("has_live_ready_manifest") and not has_demo_only_manifest:
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\admin_service.py:141: if str(row.get("country") or "").strip().lower() == "england"
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\admin_service.py:317: link = landhub_links.get(row.listing_id)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\admin_service.py:318: parcel = parcel_lookup.get(link.parcel_id) if link else None
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\cost_engine_service.py:87: value = payload.get(key)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\cost_engine_service.py:194: source_id = str(row.get("source_id") or "").strip()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\cost_engine_service.py:197: obj = db.get(CostSourceRegistry, source_id)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\cost_engine_service.py:201: source_type = str(row.get("source_type") or "unknown").strip()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\cost_engine_service.py:202: obj.source_name = str(row.get("source_name") or source_id).strip()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\cost_engine_service.py:203: obj.source_url = str(row.get("source_url") or "N/A").strip()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\cost_engine_service.py:205: obj.coverage = str(row.get("coverage") or "").strip() or None
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\cost_engine_service.py:206: obj.published_or_updated_date = _parse_date(row.get("published_or_updated_date"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\cost_engine_service.py:207: obj.reliability_base = _to_float(row.get("reliability_base"), 0.0)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\cost_engine_service.py:208: obj.is_seed_based = _is_seed_row(source_id, row.get("notes"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\cost_engine_service.py:210: obj.notes = str(row.get("notes") or "").strip() or None
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\cost_engine_service.py:231: source_id = str(row.get("source_id") or "").strip() or None
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\export_market_geometry.py:10: from shapely.ops import transform as shapely_transform
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\export_market_geometry.py:39: match_hints = metadata.get("match_hints")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\export_market_geometry.py:40: raw_record = metadata.get("raw_record")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\export_market_geometry.py:48: parsed = parse_geojson_value(container.get(key))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\export_market_geometry.py:61: geo_type = str(geojson.get("type") or "").strip()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\facility_catalog.py:350: return FACILITY_SOURCE_SETTINGS.get(source_name, {"label": source_name, "source_priority": "open", "is_official": False, "default_category": None})
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\facility_resolution.py:41: return SOURCE_PRIORITY_RANK.get(_safe_text(value).lower(), 0)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\facility_resolution.py:45: point_geometry = record.get("point_geometry")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\facility_resolution.py:48: site_geometry = record.get("site_geometry")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\facility_resolution.py:55: site_geometry = record.get("site_geometry")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\facility_resolution.py:68: postcode = normalize_postcode(record.get("postcode"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\facility_resolution.py:69: address = normalize_token(record.get("address_text"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\facility_resolution.py:70: authority = normalize_token(record.get("local_authority"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\facility_resolution.py:81: uprn = normalize_token(record.get("uprn"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\facility_resolution.py:84: toid = normalize_token(record.get("toid"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\facility_resolution.py:87: usrn = normalize_token(record.get("usrn"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\facility_resolution.py:95: authority = normalize_token(record.get("local_authority")) or "unknown"
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\facility_resolution.py:98: category = normalize_token(record.get("category_code")) or "unknown"
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\facility_scoring.py:69: return summary.get(metric_name)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\facility_scoring.py:73: weights = dict(profile.get("weights_json") or {})
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\facility_scoring.py:74: base_score = float(weights.get("base_score", 50.0))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\facility_scoring.py:75: positive_rules = dict(weights.get("positive") or {})
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\facility_scoring.py:76: negative_rules = dict(weights.get("negative") or {})
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\facility_scoring.py:77: dominant_context_bonuses = dict(weights.get("dominant_context_bonuses") or {})
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\facility_scoring.py:78: dominant_context_penalties = dict(weights.get("dominant_context_penalties") or {})
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\facility_scoring.py:79: mix_adjustment_weight = float(weights.get("mix_adjustment_weight", 0.0))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\facility_scoring.py:80: dominant_context = summary.get("dominant_context_code")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\facility_scoring.py:87: kind = str(rule.get("kind") or "ratio_positive")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\facility_scoring.py:90: normalized = handler(raw_value, float(rule.get("threshold") or rule.get("target") or 1.0))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\facility_scoring.py:91: contribution = float(rule.get("weight", 0.0)) * normalized
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\facility_service.py:41: BULK_INSERT_CHUNK_ROWS = max(int(os.environ.get("FACILITY_BULK_INSERT_CHUNK_ROWS", "8000")), 500)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\facility_service.py:43: os.environ.get("FACILITY_SKIP_PER_BATCH_CONTEXT_DELETE", "false").strip().lower() in {"1", "true", "yes", "on"}
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\facility_service.py:61: row = existing.get(definition["category_code"])
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\facility_service.py:77: row = existing.get(definition["profile_code"])
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\facility_service.py:83: row.description = payload.get("description")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\facility_service.py:85: row.is_default = bool(payload.get("is_default", False))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\facility_service.py:155: source_url=payload.get("source_url"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\facility_service.py:156: source_updated_at=payload.get("source_updated_at"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\facility_service.py:157: ingested_at=payload.get("ingested_at"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\facility_service.py:158: match_method=payload.get("match_method"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\facility_service.py:159: match_score=payload.get("match_score"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\facility_service.py:160: confidence_score=payload.get("confidence_score"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\listing_area.py:62: numeric = _to_positive_float(container.get(key))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\listing_area.py:71: hints = metadata.get("match_hints")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\listing_area.py:72: raw_record = metadata.get("raw_record")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\listing_service.py:37: raw_record = metadata.get("raw_record") if isinstance(metadata.get("raw_record"), dict) else {}
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\listing_service.py:39: _clean_text(raw_record.get("source_polygon_original_site_status"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\listing_service.py:40: or _clean_text(metadata.get("source_polygon_original_site_status"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\listing_service.py:43: _clean_text(raw_record.get("source_polygon_origin"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\listing_service.py:44: or _clean_text(metadata.get("source_polygon_origin"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\listing_service.py:47: _clean_text(raw_record.get("sale_footprint_geojson"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\listing_service.py:48: or _clean_text(raw_record.get("footprint_geojson"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\listing_service.py:49: or _clean_text(raw_record.get("listing_plan_polygon_geojson"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\listing_service.py:52: has_parcel_match = bool(matched.get("matched_parcel_ref") or matched.get("matched_inspire_id"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\listing_service.py:155: current = best_by_key.get(key)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\listing_service.py:313: matched_parcel_id = matched.get("matched_parcel_id")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\listing_service.py:319: "source_polygon_original_site_status": provenance.get("source_polygon_original_site_status") or "derived_from_parcel_match",
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\listing_truth.py:283: resolved_url = item.get("external_url") or item.get("listing_url") or item.get("source_url")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\listing_truth.py:285: source_name=item.get("source_name"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\listing_truth.py:286: provider_name=item.get("provider_name"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\listing_truth.py:287: provider_kind=item.get("provider_kind"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\listing_truth.py:288: truth_tier=item.get("truth_tier") or item.get("source_tier"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\listing_truth.py:289: is_demo=item.get("is_demo"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\listing_truth.py:297: }.get(source_tier, 0)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\listing_truth.py:298: link_info = item.get("link_truth") if isinstance(item.get("link_truth"), dict) else build_link_truth(
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\listing_truth.py:299: source_name=item.get("source_name"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\listing_truth.py:301: provider_name=item.get("provider_name"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\listing_truth.py:302: provider_kind=item.get("provider_kind"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\listing_truth.py:304: is_demo=item.get("is_demo"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\managed_sales_repository.py:64: raw_id = str(row.get("id") or "").strip()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\managed_sales_repository.py:68: "listing_title": str(row.get("listing_title") or "").strip() or "Untitled listing",
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\managed_sales_repository.py:69: "site_name": row.get("site_name"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\managed_sales_repository.py:70: "parcel_name": row.get("parcel_name"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\managed_sales_repository.py:71: "region_slug": str(row.get("region_slug") or "england").strip() or "england",
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\managed_sales_repository.py:72: "local_authority": row.get("local_authority"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\managed_sales_repository.py:73: "parcel_ref": row.get("parcel_ref"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\managed_sales_repository.py:74: "inspire_id": row.get("inspire_id"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\managed_sales_repository.py:75: "address_text": row.get("address_text"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\managed_sales_repository.py:76: "listing_status": str(row.get("listing_status") or "on_market").strip() or "on_market",
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\managed_sales_repository.py:77: "asking_price_gbp": _to_decimal(row.get("asking_price_gbp"), "0.01"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\managed_sales_repository.py:78: "guide_price_gbp": _to_decimal(row.get("guide_price_gbp"), "0.01"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\parcel_service.py:80: cached_label = str((cached_use or {}).get("label") or "").strip().lower()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\parcel_service.py:93: model = SOURCE_DETAIL_MODELS.get(source_name)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\parcel_service.py:276: tier = str(record.get("source_tier") or record.get("truth_tier") or "").strip().lower()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\parcel_service.py:277: is_demo = bool(record.get("is_demo")) or tier == "demo"
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\parcel_service.py:283: price_truth = record.get("price_truth") if isinstance(record.get("price_truth"), dict) else {}
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\parcel_service.py:284: if price_truth.get("is_real") is not True or not has_price(record.get("ask_price")):
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\parcel_service.py:316: all_active_sale_records = summary.get("active_sale_records", []) if isinstance(summary.get("active_sale_records"), list) else []
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\parcel_service.py:323: official_visible_count = sum(1 for record in filtered_active_sale_records if record.get("source_tier") == "official")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\parcel_service.py:324: market_visible_count = sum(1 for record in filtered_active_sale_records if record.get("source_name") == "market_listing_adapter")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\parcel_service.py:325: sale_summary = deepcopy(summary.get("sale_summary") or {})
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\parcel_service.py:327: top_actionable_truth = top_actionable_listing.get("price_truth") if isinstance(top_actionable_listing, dict) else {}
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\parcel_service.py:332: if isinstance(record.get("price_truth"), dict) and record["price_truth"].get("is_real") is True and has_price(record.get("ask_price"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\parcel_use_classifier.py:44: return payload.get(key, default)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\parcel_use_classifier.py:153: for target_label, bonus in DOMINANT_CONTEXT_BONUS.get(dominant_context, {}).items():
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\parcel_use_classifier.py:158: target_label = SCENARIO_TO_USE_LABEL.get(profile_code)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\parcel_use_classifier.py:190: key=lambda item: abs(item.get("impact", 0.0)),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\planned_asset_scoring.py:143: }.get(normalized, 18.0)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\planned_asset_scoring.py:210: type_weight = ASSET_TYPE_WEIGHTS.get(str(asset_type or "").strip(), 0.42)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\planned_asset_scoring.py:352: }.get(normalized, 68.0)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\planned_asset_service.py:74: planning_ref = _clean_text(payload.get("planning_reference"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\planned_asset_service.py:77: title = _clean_text(payload.get("title"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\planned_asset_service.py:78: authority = _clean_text(payload.get("local_authority"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\planned_asset_service.py:79: postcode = _clean_text(payload.get("postcode"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\planned_asset_service.py:160: if record.get("geometry_wkt"):
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\planned_asset_service.py:162: if record.get("centroid_lat") is not None and record.get("centroid_lon") is not None:
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\planned_asset_service.py:178: value = metadata_json.get(key)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\planned_asset_service.py:187: if not str(record.get("source_url") or "").strip():
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\planned_asset_service.py:189: if not str(record.get("evidence_text") or "").strip():
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\planned_asset_service.py:210: planned_start_year=normalized.get("planned_start_year"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\planned_asset_service.py:211: planned_completion_year=normalized.get("planned_completion_year"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\planned_asset_service.py:212: estimated_window_start=normalized.get("estimated_delivery_window_start"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\planned_source_registry.py:231: row = existing.get(payload["source_id"])
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\runtime_ops_service.py:12: from app.schemas.ops import (
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\runtime_ops_service.py:44: value = str(payload.get("landIntelligenceApiBaseUrl") or "").strip()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\runtime_ops_service.py:49: value = payload.get(key)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\runtime_ops_service.py:88: contractor_preflight_path=_registry_value(
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\runtime_ops_service.py:90: "contractor_preflight_path",
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\runtime_ops_service.py:91: str(settings.contractor_preflight_audit_path),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\runtime_ops_service.py:132: _path_check("contractor_preflight_path", registry.contractor_preflight_path),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\sale_land_verification.py:57: value = record.get(key)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\sale_land_verification.py:121: if _has_value(record, "review_status") and str(record.get("review_status")).lower() in {"approved", "verified"}:
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\sale_land_verification.py:126: source_area = _as_float(record.get("area_m2") or record.get("area_sq_m"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\sale_land_verification.py:127: geom_area = _as_float(record.get("geometry_area_m2"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\sale_link_utils.py:11: attrs = (getattr(record, 'metadata_json', None) or {}).get('raw_attributes', {})
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\sale_link_utils.py:12: contact_details = str(attrs.get('Contact_Details') or '').strip()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\sale_link_utils.py:19: drone_footage = str(attrs.get('DroneFootage') or '').strip()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\scoring.py:20: return SOURCE_RELIABILITY.get(source_name, 0.6)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\source_catalog.py:127: return STALE_THRESHOLDS.get(source_name, 90)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\source_manifest_status.py:59: explicit_mode = str(entry.get("mode") or "").strip().lower()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\source_manifest_status.py:62: if entry.get("download_url") or entry.get("download_urls"):
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\source_manifest_status.py:69: primary = entry.get("download_url")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\source_manifest_status.py:72: extras = entry.get("download_urls")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\source_manifest_status.py:85: active_entries = [entry for entry in entries if bool(entry.get("active", True))]
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\source_manifest_status.py:89: resolved_path = resolve_manifest_file(manifest_path, entry.get("file_drop_path"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\source_manifest_status.py:92: provider_name=entry.get("provider_name"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\source_manifest_status.py:93: provider_kind=entry.get("provider_kind"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\source_manifest_status.py:94: truth_tier=entry.get("truth_tier"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\source_manifest_status.py:95: is_demo=entry.get("is_demo"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\source_manifest_status.py:96: url=str(resolved_path or entry.get("file_drop_path") or ""),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\source_manifest_status.py:99: if bool(entry.get("active", True)) and not file_exists:
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\source_service.py:43: latest = latest_by_source.get(name)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\source_service.py:47: stale_days = threshold_map.get(name, STALE_THRESHOLDS.get(name, 30))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\supabase_admin_service.py:262: data = result.get("data")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\supabase_admin_service.py:360: data = result.get("data")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\supabase_sync_service.py:32: candidate.metadata.get("source_record_id")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\supabase_sync_service.py:48: candidate.metadata.get("source_record_id")

## Recommended patch plan
- Add a read-only contractor export service under app/services.
- Add a read-only API router under the detected app API/router structure.
- Return CSV/JSONL-backed summaries without exposing suppressed contact fields.
- Keep DO_NOT_CONTACT gate unchanged; do not alter source export files.
