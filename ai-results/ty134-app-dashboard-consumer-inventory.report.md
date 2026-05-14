# TY134 App Dashboard Consumer Inventory

Plan completed: 45%
Plan remaining: 55%

## Export readiness
- E:\AAYS_DATA\contractor\exports\contractors_for_app.csv bytes=63729 modified=2026-05-14T13:21:38
- E:\AAYS_DATA\contractor\exports\contractors_for_app.jsonl bytes=280330 modified=2026-05-14T13:21:42
- E:\AAYS_DATA\contractor\exports\contractor_projects_for_app.csv bytes=405940 modified=2026-05-14T13:21:42
- E:\AAYS_DATA\contractor\exports\contractor_parcel_matches_for_app.csv bytes=5688 modified=2026-05-14T13:21:42
- E:\AAYS_DATA\contractor\exports\export_manifest.json bytes=867 modified=2026-05-14T13:21:42

## Consumer/code hits
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\main.py:11: from app.api.routes import admin, brownfield, contractor, cost, etl, facilities, future_growth, health, listings, map_layers, ops, parcels, planned_assets, proxy, sources
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\main.py:12: from app.api.routes import aays_sales_layers
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\main.py:20: description="Parcel-centric land opportunity intelligence service for TerraYield",
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\main.py:31: app.include_router(health.router)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\main.py:32: app.include_router(sources.router)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\deps.py:23: detail="Admin token configured degil. Write route'lar fail-closed durumda.",
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\aays_sales_history_layers.py:7: from fastapi import APIRouter, HTTPException
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\aays_sales_history_layers.py:16: router = APIRouter(tags=["aays-sales-history"])
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\aays_sales_history_layers.py:34: to_regclass('public.parcels_inspire') IS NOT NULL AS has_parcels,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\aays_sales_history_layers.py:35: to_regclass('public.parcel_external_market_evidence_summary') IS NOT NULL AS has_external
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\aays_sales_history_layers.py:40: if row and row["has_parcels"] and row["has_external"]:
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\aays_sales_layers.py:5: from fastapi import APIRouter
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\aays_sales_layers.py:10: router = APIRouter(tags=["aays-sales-layers"])
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\aays_sales_layers.py:33: @router.get("/map/sales-layers/external-market")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\aays_sales_layers.py:44: p.parcel_id,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\aays_sales_layers.py:45: p.parcel_ref,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\aays_sale_land_verification.py:3: from fastapi import APIRouter
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\aays_sale_land_verification.py:7: router = APIRouter(prefix="/verification/sale-land", tags=["sale-land-verification"])
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\aays_sale_land_verification.py:10: @router.post("/classify")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\admin.py:3: from fastapi import APIRouter, Depends, HTTPException, Query
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\admin.py:11: ParcelLinkingRebuildRequest,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\admin.py:12: ParcelLinkingRebuildResult,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\admin.py:13: ParcelLinkingStatus,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\admin.py:23: from app.services.parcel_linking_service import get_parcel_linking_status, rebuild_parcel_links_and_signals
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\brownfield.py:3: from fastapi import APIRouter, Query
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\brownfield.py:10: router = APIRouter(prefix='/brownfield-sites', tags=['brownfield'])
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\brownfield.py:20: @router.get('', response_model=None)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\brownfield.py:46: @router.get('/{site_id}', response_model=BrownfieldSiteDetail)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\contractor.py:8: from fastapi import APIRouter, HTTPException, Query
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\contractor.py:11: from app.schemas.contractor import (
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\contractor.py:12: ContractorExportRowsResponse,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\contractor.py:13: ContractorParcelContactsResponse,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\contractor.py:14: ContractorStatusResponse,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\cost.py:3: from fastapi import APIRouter, Depends, HTTPException, Query
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\cost.py:14: Cost50ParcelsSummary,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\cost.py:24: ParcelCostEstimateHistoryItem,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\cost.py:27: estimate_parcel_cost,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\cost.py:33: get_parcel_cost_history,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\etl.py:3: from fastapi import APIRouter, Query
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\etl.py:9: router = APIRouter(prefix='/etl', tags=['etl'])
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\etl.py:12: @router.post('/run', response_model=list[ETLRunResponse])
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\etl.py:17: @router.get('/runs', response_model=list[ETLRunResponse])
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\facilities.py:3: from fastapi import APIRouter, Query
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\facilities.py:10: router = APIRouter(prefix="/facilities", tags=["facilities"])
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\facilities.py:13: @router.get("", response_model=None)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\future_growth.py:5: from fastapi import APIRouter, HTTPException, Query, status
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\future_growth.py:23: FutureGrowthParcelDetailResponse,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\future_growth.py:27: router = APIRouter(prefix="/api/future-growth", tags=["future-growth"])
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\future_growth.py:37: @router.get("/layer", response_model=FutureGrowthLayerResponse)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\future_growth.py:59: @router.get("/parcels/{parcel_id}", response_model=FutureGrowthParcelDetailResponse)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\health.py:3: from fastapi import APIRouter
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\health.py:10: router = APIRouter(tags=['health'])
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\health.py:13: @router.get('/health', response_model=HealthResponse)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\listings.py:3: from fastapi import APIRouter, Query
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\listings.py:9: from app.services.supabase_admin_service import list_supabase_parcel_records
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\listings.py:12: router = APIRouter(prefix='/listings', tags=['listings'])
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\listings.py:22: @router.get('', response_model=None)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\listings.py:66: @router.get('/managed-sales', response_model=list[SupabaseLandListingRecord])
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\map_layers.py:3: from fastapi import APIRouter, Query
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\map_layers.py:9: from app.services.parcel_service import list_parcels
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\map_layers.py:11: router = APIRouter(prefix='/map', tags=['map'])
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\map_layers.py:21: @router.get('/parcels', response_model=GeoJSONFeatureCollection)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\map_layers.py:22: def get_map_parcels(
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\ops.py:3: from fastapi import APIRouter, Query
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\ops.py:13: router = APIRouter(prefix="/ops", tags=["ops"])
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\ops.py:16: @router.get("/storage-registry", response_model=RuntimeStorageRegistryResponse)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\ops.py:21: @router.get("/consistency-check", response_model=RuntimeConsistencyCheckResponse)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\parcels.py:3: from fastapi import APIRouter, Query
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\parcels.py:7: from app.schemas.facility import ParcelContextSummaryItem, ParcelScenarioScoreItem
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\parcels.py:8: from app.schemas.parcel import ParcelDetail, ParcelHistoryItem, ParcelListItem, ParcelSignalItem
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\parcels.py:9: from app.services.facility_service import get_parcel_context, get_parcel_scores
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\parcels.py:10: from app.services.parcel_service import get_parcel_detail, get_parcel_history, get_parcel_signals, list_parcels
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\planned_assets.py:3: from fastapi import APIRouter, Depends, Query
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\planned_assets.py:7: ParcelFutureGrowthScoreResponse,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\planned_assets.py:16: get_parcel_future_growth_score,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\planned_assets.py:17: get_parcel_planned_assets,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\planned_assets.py:26: router = APIRouter(tags=["planned-assets"])
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\proxy.py:6: from fastapi import APIRouter, HTTPException, Request
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\proxy.py:10: PARCEL_PROXY_BASE_URL = "https://terrayield-demo.cagdascagiaydin.workers.dev/parcels"
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\proxy.py:12: LOCAL_PARCEL_FILES = {
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\proxy.py:13: "midlands.pmtiles": REPO_ROOT / "data" / "inspire" / "region_jobs" / "midlands" / "tiles" / "parcels.pmtiles",
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\proxy.py:15: PARCEL_DIRECT_URLS = {
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\sources.py:3: from fastapi import APIRouter
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\sources.py:9: router = APIRouter(prefix='/sources', tags=['sources'])
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\sources.py:12: @router.get('', response_model=list[SourceDescriptor])
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\sources.py:17: @router.get('/status', response_model=list[SourceStatus])
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\core\config.py:139: future_growth_max_parcel_batch: int = 5000
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\core\config.py:140: future_growth_vector_min_parcels: int = 8
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\core\config.py:158: contractor_storage_root: Path = Field(default_factory=lambda: Path(r'E:\AAYS_DATA\contractor'))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\core\config.py:159: contractor_export_root: Path | None = None
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\core\config.py:160: contractor_manifest_root: Path | None = None
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\db\models.py:33: class ParcelInspire(Base, TimestampMixin):
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\db\models.py:34: __tablename__ = "parcels_inspire"
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\db\models.py:36: parcel_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\db\models.py:38: parcel_ref: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\db\models.py:62: parcel_name: Mapped[str | None] = mapped_column(Text, nullable=True)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\apply_repo_manual_match_overrides.py:65: "matched_parcel_ref",
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\apply_repo_manual_match_overrides.py:90: parser = argparse.ArgumentParser(description="Apply manual repo listing-to-parcel overrides onto a CSV batch.")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\authority_checkpoint.py:36: csv_path = checkpoint_dir / "parcels_inspire.csv"
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\authority_checkpoint.py:45: parcel_ref,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\authority_checkpoint.py:61: FROM parcels_inspire
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\authority_checkpoint.py:63: ORDER BY parcel_id
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\authority_checkpoint.py:68: row_count = count_parcels_for_authority(authority)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\boost_parcel_use_from_facilities.py:14: SELECT parcel_id, geometry
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\boost_parcel_use_from_facilities.py:15: FROM parcels_inspire
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\boost_parcel_use_from_facilities.py:32: SELECT l.parcel_id, nf.label, nf.dist
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\boost_parcel_use_from_facilities.py:42: UPDATE parcel_use_inference pui
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\boost_parcel_use_from_facilities.py:43: SET parcel_use_label = nearest.label,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\bootstrap_homes_england_handoff.py:12: from app.etl.authority_checkpoint import count_parcels_for_authority
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\bootstrap_homes_england_handoff.py:54: if count_parcels_for_authority(authority) > 0:
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\build_authority_subset_manifest.py:54: for row in conn.execute(text("select distinct local_authority from parcels_inspire where local_authority is not null"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\build_authority_subset_manifest.py:101: parser.add_argument("--only-missing", action="store_true", help="Keep only authorities not yet loaded in parcels_inspire.")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\build_england_region_chunk_matrix.py:8: from app.db.models import ParcelInspire
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\build_england_region_chunk_matrix.py:10: from app.etl.england_region_partitions import parse_region_codes, parcel_scope_filters
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\build_england_region_chunk_matrix.py:33: help="Skip matrix rows where target parcel count is zero.",
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\build_england_region_chunk_matrix.py:51: func.mod(ParcelInspire.parcel_id, args.chunk_count_per_region).label("chunk_index"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\build_england_region_chunk_matrix.py:57: for scope_filter in parcel_scope_filters(args.country, region_code):
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\build_market_integration_package.py:75: return "source_mostly_covered_by_parcel"
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\build_market_integration_package.py:95: parcel_origin: str,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\build_market_integration_package.py:101: if parcel_origin == "official.parcels_inspire":
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\build_market_integration_package.py:104: f"parcel link is official ({match_origin})."
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\build_market_integration_package.py:108: f"parcel link is provisional ({match_origin})."
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\build_market_polygon_provenance.py:37: return bool(_clean(row.get("matched_parcel_ref")) or _clean(row.get("matched_inspire_id")))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\build_market_polygon_provenance.py:90: def _parcel_origin(record_state: str) -> str:
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\build_market_polygon_provenance.py:92: return "official.parcels_inspire"
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\build_market_polygon_provenance.py:94: return "not_linked_official_parcel"
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\build_market_polygon_provenance.py:205: "parcel_polygon_origin": _parcel_origin(record_state),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\england_all_sales_candidate_geometry_builder.py:493: (exp / "ENGLAND_ESTIMATED_CANDIDATE_dashboard.html").write_text(make_html(summary, outputs), encoding="utf-8")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\england_deep_sales_source_confidence_booster.py:128: note=(f"DEEP_ENGLAND_SALES_SOURCE_CONFIDENCE | score={score['deep_confidence_score']} | tier={score['deep_confidence_tier']} | label={score['deep_confidence_label']} | source_area={score['source_area']} | plan_signal={score['plan_signal']} | public_doc={score['public_doc_downloaded']} | reference={score['reference_signal']} | polygon_signal={score['polygon_signal']} | area_hits={score['area_hits']} | area={clean(row.get('estimated_area_m2'))}m2 | perimeter={clean(row.get('perimeter_m'))}m | sides_m={clean(row.get('side_lengths_m_json'))} | sides_cm={clean(row.get('side_lengths_cm_json'))} | NOT official parcel match; non-A rows remain estimated sale geometry candidates.")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\england_deep_sales_source_confidence_booster.py:140: summary={"finished_at":dt.datetime.now(dt.timezone.utc).isoformat(),"rows":len(ranked),"tier_counts":counts,"apply_rows":len(apply_rows),"evidence_jsonl":"/app/data/live_feeds/exports/ENGLAND_DEEP_SALES_SOURCE_EVIDENCE.jsonl","important":"Deep pass still does not use official parcel system as proof. A/A? rows need validation before claiming original boundary.","outputs":{"ranked_csv":"/app/data/live_feeds/exports/ENGLAND_DEEP_SALES_SOURCE_CONFIDENCE_RANKED.csv","apply_csv":"/app/data/live_feeds/exports/ENGLAND_DEEP_SALES_SOURCE_STRICT_APPLY.csv","dashboard":"/app/data/live_feeds/exports/ENGLAND_DEEP_SALES_SOURCE_CONFIDENCE_RANKED.html"}}
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\england_region_partitions.py:7: from app.db.models import ParcelInspire
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\england_region_partitions.py:62: def parcel_country_filter(country: str, *, model=ParcelInspire):
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\england_region_partitions.py:69: def parcel_region_filter(region_code: str | None, *, model=ParcelInspire):
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\england_region_partitions.py:81: def parcel_scope_filters(country: str, region_code: str | None, *, model=ParcelInspire) -> list:
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\england_region_partitions.py:83: country_filter = parcel_country_filter(country, model=model)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\england_sales_source_discovery_and_geometry.py:135: # Count only plausible candidate sizes or keyword tables, avoid huge parcel tables.
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\england_sales_source_discovery_and_geometry.py:508: (exports / "ENGLAND_ESTIMATED_CANDIDATE_dashboard.html").write_text(make_html(summary, outputs), encoding="utf-8")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\enrich_public_listing_addresses.py:38: if _clean(row.get("matched_parcel_ref")) or _clean(row.get("matched_inspire_id")):
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\enrich_public_listing_addresses.py:102: parcel_name = _clean(row.get("parcel_name"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\enrich_public_listing_addresses.py:112: if parcel_name and address_text and parcel_name.lower() not in address_text.lower():
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\enrich_public_listing_addresses.py:113: candidates.append(f"{parcel_name}, {address_text}")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\enrich_public_listing_addresses.py:118: if postcode and parcel_name:
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\estimated_candidate_geometry_builder.py:152: summary={'finished_at':dt.datetime.now(dt.timezone.utc).isoformat(),'rows':len(rows),'generated_candidate_polygons':len(rows),'verified_original_polygons':0,'important':'Estimated derived candidate polygons, not verified original site boundaries.','confidence_counts':{},'method_counts':{},'outputs':{'candidate_csv':'/app/data/live_feeds/exports/ESTIMATED_CANDIDATE_sale_polygons_all164.csv','candidate_geojson':'/app/data/live_feeds/exports/ESTIMATED_CANDIDATE_sale_polygons_all164.geojson','apply_csv':'/app/data/live_feeds/exports/ESTIMATED_CANDIDATE_apply_as_derived_all164.csv','dashboard':'/app/data/live_feeds/exports/ESTIMATED_CANDIDATE_dashboard.html'}}
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\estimated_candidate_geometry_builder.py:157: (exports/'ESTIMATED_CANDIDATE_dashboard.html').write_text(make_html(summary,rows),encoding='utf-8')
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\export_final_after_d_upgrade.py:45: "Official parcel system is not treated as proof. "
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\export_market_listing_parcel_package.py:44: "matched_parcel_id",
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\export_market_listing_parcel_package.py:45: "matched_parcel_ref",
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\export_market_listing_parcel_package.py:52: "parcel_area_m2",
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\export_market_listing_parcel_package.py:53: "parcel_perimeter_m",
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\export_market_listing_parcel_package.py:54: "parcel_centroid_lat",
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\fill_market_listing_export_gaps.py:82: parcel_area = _to_float(row.get("parcel_area_m2"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\fill_market_listing_export_gaps.py:83: if parcel_area is not None and parcel_area > 0:
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\fill_market_listing_export_gaps.py:84: return _format_float(parcel_area, digits=3), _format_float(parcel_area / ACRE_TO_M2, digits=6), "proxy_from_matched_parcel_area"
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\fill_market_listing_export_gaps.py:98: centroid_lat = _to_float(row.get("parcel_centroid_lat"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\fill_market_listing_export_gaps.py:99: centroid_lon = _to_float(row.get("parcel_centroid_lon"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\final_3110_fail_closed_l4_pipeline.py:499: out["parcel_geometry"] = {
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\full_autonomous_polygon_classifier.py:213: "dashboard": "/app/data/live_feeds/exports/FULL_AUTONOMOUS_dashboard.html",
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\full_autonomous_polygon_classifier.py:217: (exports / "FULL_AUTONOMOUS_dashboard.html").write_text(make_html(summary, verified, candidates, low), encoding="utf-8")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\import_final_sale_geometry_confidence_table.py:124: <p>Official parcel system is not treated as proof. Non-A rows are estimated sale-geometry candidates.</p>
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\import_final_sale_geometry_confidence_table.py:165: "important": "Official parcel system is not treated as proof. A? requires validation before claiming original boundary. Non-A rows are estimated sale-geometry candidates.",
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\load_external_market_sales_evidence.py:50: parcel_ref = first(row, ["matched_parcel_ref", "parcel_ref"])
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\load_external_market_sales_evidence.py:65: if parcel_ref or inspire_id:
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\load_external_market_sales_evidence.py:123: "matched_parcel_ref": first(row, ["matched_parcel_ref", "parcel_ref"]),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\load_external_market_sales_evidence.py:137: "evidence_chain": "external_market_source_csv -> optional parcel_ref/inspire_id -> parcels_inspire",
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\load_external_market_sales_evidence.py:150: matched_parcel_ref text,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_autonomous_polygon_finalize.py:225: "dashboard_html": str(out_dir / "autonomous_london_polygon_dashboard.html"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_autonomous_polygon_finalize.py:230: html = _dashboard_html(summary, verified_rows, candidate_rows, low_rows)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_autonomous_polygon_finalize.py:231: (out_dir / "autonomous_london_polygon_dashboard.html").write_text(html, encoding="utf-8")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_autonomous_polygon_finalize.py:237: def _dashboard_html(summary: dict[str, Any], verified: list[dict[str, Any]], candidates: list[dict[str, Any]], lows: list[dict[str, Any]]) -> str:
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_autonomous_polygon_finalize.py:255: <html><head><meta charset="utf-8"><title>Autonomous London Polygon Dashboard</title>
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_deep_sales_source_confidence_booster.py:204: # Strictly sale-source evidence. No official parcel match used.
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_deep_sales_source_confidence_booster.py:249: "source area/ref/plan signals only; official parcel system is not proof."
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_deep_sales_source_confidence_booster.py:322: f"NOT official parcel match; non-A rows remain estimated sale geometry candidates."
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_deep_sales_source_confidence_booster.py:368: "important": "Deep pass still does not use official parcel system as proof. A/A? rows need validation before claiming original boundary.",
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_deep_sales_source_confidence_booster.py:372: "dashboard": "/app/data/live_feeds/exports/LONDON_DEEP_SALES_SOURCE_CONFIDENCE_RANKED.html",
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_market_polygon_verification_batch.py:17: from app.db.models import ListingParcelLink, ListingsMarketAdapter, ParcelInspire
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_market_polygon_verification_batch.py:135: ListingParcelLink.listing_id.label("listing_id"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_market_polygon_verification_batch.py:136: ListingParcelLink.source_record_id.label("source_record_id"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_market_polygon_verification_batch.py:137: ListingParcelLink.match_method.label("match_method"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_market_polygon_verification_batch.py:138: ListingParcelLink.confidence_score.label("confidence_score"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_polygon_accuracy_diagnostic.py:17: from app.db.models import ParcelInspire
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_polygon_accuracy_diagnostic.py:92: return "centroid_inside_official_parcel_candidate"
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_polygon_accuracy_diagnostic.py:94: return "nearest_official_parcel_very_close"
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_polygon_accuracy_diagnostic.py:96: return "nearest_official_parcel_close"
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_polygon_accuracy_diagnostic.py:98: return "nearest_official_parcel_review_needed"
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_polygon_candidate_generator.py:22: from app.db.models import ParcelInspire
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_polygon_candidate_generator.py:110: if re.search(r"\b(plot|site|land|parcel|total plot|plot size)\b", context, re.I):
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_polygon_candidate_generator.py:351: reasons.append("centroid_inside_official_parcel")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_polygon_candidate_generator.py:427: distance_expr = func.ST_Distance(ParcelInspire.geometry, point_27700)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_polygon_candidate_generator.py:428: contains_expr = func.ST_Contains(ParcelInspire.geometry, point_27700)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_polygon_srid_postcode_diagnostic.py:18: from app.db.models import ParcelInspire
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_polygon_srid_postcode_diagnostic.py:107: def _text_match_score(row: dict[str, str], parcel_postcode: str, parcel_la: str) -> tuple[float, list[str]]:
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_polygon_srid_postcode_diagnostic.py:112: pp = _clean(parcel_postcode).upper()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_polygon_srid_postcode_diagnostic.py:115: pla = _clean(parcel_la).lower()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_polygon_srid_postcode_diagnostic.py:175: select(func.ST_SRID(ParcelInspire.geometry).label("srid"), func.count().label("count"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_real_site_polygon_verifier.py:32: from app.db.models import ParcelInspire
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_real_site_polygon_verifier.py:91: "derived_parcel_ref",
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_real_site_polygon_verifier.py:401: def derive_from_official_parcel(
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_real_site_polygon_verifier.py:411: distance_expr = func.ST_Distance(func.ST_Centroid(ParcelInspire.geometry), point)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_real_site_polygon_verifier.py:412: contains_expr = func.ST_Contains(ParcelInspire.geometry, point)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_site_derived_polygon_miner.py:22: from app.db.models import ListingsMarketAdapter, ParcelInspire
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_site_derived_polygon_miner.py:271: has_plot_words = bool(re.search(r"\b(plot|land|site|parcel|freehold|tenure)\b", text_norm, re.I))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_site_derived_polygon_miner.py:307: return "high", f"centroid_inside_official_parcel; {area_note}; strong_site_evidence"
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_site_derived_polygon_miner.py:310: return "high", f"near_centroid_official_parcel; distance_m={distance_m:.2f}; {area_note}; strong_site_evidence"
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\london_site_derived_polygon_miner.py:313: return "medium", f"centroid_inside_official_parcel; {area_note}; area_match_medium"
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\match_external_market_polygons_to_parcels.py:12: MATCH_TABLE = "external_market_polygon_parcel_matches"
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\match_external_market_polygons_to_parcels.py:123: parcel_srid = c.execute(text("""
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\match_external_market_polygons_to_parcels.py:125: from parcels_inspire
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\match_external_market_polygons_to_parcels.py:130: print(f"parcel_srid={parcel_srid}")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\match_external_market_polygons_to_parcels.py:145: source_geom_parcel_srid geometry,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\orchestrator.py:16: ListingParcelLink,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\orchestrator.py:20: ParcelInspire,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\orchestrator.py:21: ParcelSignalSummary,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\orchestrator.py:29: from app.etl.match.parcel_matcher import match_source_records
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\orchestrator.py:30: from app.etl.publish.parcel_signal_summary import refresh_parcel_signal_summary
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\prepare_homes_england_handoff.py:9: from app.etl.authority_checkpoint import count_parcels_for_authority, export_authority_checkpoint
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\prepare_homes_england_handoff.py:62: parcel_count = count_parcels_for_authority(authority)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\prepare_homes_england_handoff.py:63: if parcel_count <= 0:
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\prepare_homes_england_handoff.py:64: raise RuntimeError(f"No imported parcel rows found for {authority}.")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\prepare_repo_manual_match_batch.py:50: for row in conn.execute(text("select distinct local_authority from parcels_inspire where local_authority is not null"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\prepare_repo_manual_match_batch.py:85: return bool((row.get("matched_parcel_ref") or "").strip() or (row.get("matched_inspire_id") or "").strip())
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\prepare_repo_manual_match_batch.py:163: parser.add_argument("--expansion-output", type=Path, default=DEFAULT_EXPANSION_OUTPUT, help="High-confidence rows that need additional parcel authorities.")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\prepare_repo_market_feed.py:31: return bool((row.get("matched_parcel_ref") or "").strip() or (row.get("matched_inspire_id") or "").strip())
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\prepare_repo_review_needed_candidates.py:35: "parcel_name",
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\prepare_repo_review_needed_candidates.py:44: "matched_parcel_ref",
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\prepare_repo_review_needed_candidates.py:154: output_row["parcel_name"] = address_text
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\prioritize_homes_england_authorities.py:49: from parcels_inspire
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\prioritize_homes_england_authorities.py:57: from listing_parcel_link
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\rebuild_parcel_links.py:7: from app.schemas.admin import ParcelLinkingRebuildRequest
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\rebuild_parcel_links.py:8: from app.services.parcel_linking_service import DEFAULT_MATCHING_SOURCES, rebuild_parcel_links_and_signals
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\rebuild_parcel_links.py:12: parser = argparse.ArgumentParser(description="Rebuild listing_parcel_link and parcel_signal_summary from existing source tables.")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\rebuild_parcel_links.py:22: help="Skip parcel_signal_summary refresh after rebuilding links.",
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\rebuild_parcel_links.py:26: payload = ParcelLinkingRebuildRequest(
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\rebuild_parcel_use_cache.py:12: from app.db.models import ParcelInspire
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\rebuild_parcel_use_cache.py:14: from app.etl.england_region_partitions import parcel_scope_filters, validate_region_code
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\rebuild_parcel_use_cache.py:16: from app.services.parcel_use_classifier import classify_parcel_use
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\rebuild_parcel_use_cache.py:19: CREATE TABLE IF NOT EXISTS parcel_use_inference (
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\rebuild_parcel_use_cache.py:20: parcel_id BIGINT PRIMARY KEY REFERENCES parcels_inspire(parcel_id) ON DELETE CASCADE,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\rebuild_parcel_use_targeted_signal_scope.py:12: from app.db.models import ListingParcelLink, ParcelInspire, ParcelSignalSummary
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\rebuild_parcel_use_targeted_signal_scope.py:14: from app.etl.england_region_partitions import parcel_scope_filters, validate_region_code
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\rebuild_parcel_use_targeted_signal_scope.py:15: from app.services.facility_service import load_context_and_scores_map, refresh_facility_context_for_parcels
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\rebuild_parcel_use_targeted_signal_scope.py:16: from app.services.parcel_use_classifier import classify_parcel_use
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\rebuild_parcel_use_targeted_signal_scope.py:19: CREATE TABLE IF NOT EXISTS parcel_use_inference (
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\recompute_facility_context_chunk.py:11: from app.db.models import ParcelInspire
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\recompute_facility_context_chunk.py:13: from app.etl.england_region_partitions import parcel_scope_filters, validate_region_code
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\recompute_facility_context_chunk.py:14: from app.services.facility_service import rebuild_resolved_facilities, refresh_facility_context_for_parcels
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\recompute_facility_context_chunk.py:36: stmt = select(func.count()).select_from(ParcelInspire).where(func.mod(ParcelInspire.parcel_id, chunk_count) == chunk_index)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\recompute_facility_context_chunk.py:37: for scope_filter in parcel_scope_filters(country, region_code):
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\run_cost_engine_pilot.py:11: from app.db.models import ParcelInspire
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\run_cost_engine_pilot.py:17: estimate_parcel_cost,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\run_cost_engine_pilot.py:22: def _resolve_parcel_ids(explicit_ids: list[int] | None, limit: int) -> list[int]:
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\run_cost_engine_pilot.py:34: select(ParcelInspire.parcel_id).order_by(ParcelInspire.parcel_id.asc()).limit(max(1, min(limit, 10)))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\run_cost_engine_pilot.py:40: parser = argparse.ArgumentParser(description="Run UK cost engine pilot for 3-10 parcels.")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\run_hmlr_inspire_low_disk.py:10: from app.db.models import ETLRun, ParcelInspire, SourceSnapshot
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\run_hmlr_inspire_low_disk.py:168: session.execute(delete(ParcelInspire).where(ParcelInspire.local_authority == authority))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\run_hmlr_inspire_low_disk.py:169: _sync_serial_sequence(session, table_name='parcels_inspire', id_column='parcel_id')
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\run_hmlr_inspire_low_disk.py:203: _sync_serial_sequence(session, table_name='parcels_inspire', id_column='parcel_id')
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\run_hmlr_inspire_low_disk.py:205: text("SELECT count(*) FROM parcels_inspire WHERE local_authority = :authority"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\run_homes_england_backfill_loop.py:16: from app.etl.authority_checkpoint import count_parcels_for_authority, export_authority_checkpoint, restore_authority_checkpoint
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\run_homes_england_backfill_loop.py:40: description="Continuously import targeted INSPIRE authorities and rebuild Homes England parcel links."
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\run_homes_england_backfill_loop.py:94: help="External-drive-friendly parcel checkpoint directory used for machine handoff.",
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\run_homes_england_backfill_loop.py:284: f"Checkpoint exported for {authority}: {checkpoint.csv_path} ({checkpoint.row_count} parcels).",
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\run_homes_england_backfill_loop.py:347: existing_count = count_parcels_for_authority(authority)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\run_planned_assets_pilot.py:16: parser.add_argument("--dry-run", action="store_true", help="Ingest without parcel matching writes.")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sold_buildings_handoff.py:15: from app.db.models import ListingParcelLink, ListingsMarketAdapter, ParcelInspire, ParcelSignalSummary, TransactionsPricePaid
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sold_buildings_handoff.py:17: from app.etl.publish.parcel_signal_summary import refresh_parcel_signal_summary
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sold_buildings_handoff.py:22: "matched_parcel_ref",
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sold_buildings_handoff.py:118: def _build_transaction_id(parcel_ref: str | None, sale_date: dt.date | None, price_paid: Decimal | None, row: dict[str, Any]) -> str:
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sold_buildings_handoff.py:121: str(parcel_ref or ""),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\split_market_batch_by_match_hints.py:9: return bool((row.get("matched_parcel_ref") or "").strip() or (row.get("matched_inspire_id") or "").strip())
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\strict_sales_geometry_confidence_ranker.py:310: f"NOT official parcel match; NOT original boundary unless tier A."
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\strict_sales_geometry_confidence_ranker.py:350: "important": "This ranking is strict: official parcel system is not treated as proof. Non-A tiers are estimated sale-geometry candidates, not verified original boundaries.",
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\strict_sales_geometry_confidence_ranker.py:354: "dashboard": "/app/data/live_feeds/exports/ENGLAND_SALE_GEOMETRY_CONFIDENCE_RANKED.html",
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\strict_sales_geometry_confidence_ranker.py:380: <p>Official parcel system is not treated as proof. Non-A rows are estimated sale-geometry candidates.</p>
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\suggest_market_batch_matches.py:23: class ParcelSuggestion:
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\suggest_market_batch_matches.py:24: parcel_ref: str
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\suggest_market_batch_matches.py:32: select parcel_ref, inspire_id
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\suggest_market_batch_matches.py:33: from parcels_inspire
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\suggest_market_batch_matches.py:34: where parcel_ref = :title_number
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sync_supabase_land_listings.py:11: parser = argparse.ArgumentParser(description="Sync parcel-linked listing seeds into local managed_land_listings compatibility store.")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sync_supabase_land_listings.py:12: parser.add_argument("--matched-only", action="store_true", help="Only sync rows that already match a parcel.")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\targeted_low_tier_visual_confidence_upgrade.py:97: note=f"TARGETED_LOW_TIER_UPGRADE | old={ot}/{os} | new={nt}/{ns} | source_area={'yes' if src_area else 'no'} | plan_signal={'yes' if plan else 'no'} | visual_boundary={'yes' if visual else 'no'} | public_doc={'yes' if doc else 'no'} | reference={'yes' if ref else 'no'} | polygon_signal={'yes' if poly else 'no'} | area_hits={'; '.join(ah[:10])} | high_value_links={len(high)} | downloads={len([d for d in dls if s(d.get('path'))])} | visual_pixels={pixels} | Official parcel system is not proof."
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\targeted_low_tier_visual_confidence_upgrade.py:121: summary={'finished_at':dt.datetime.now(dt.timezone.utc).isoformat(),'targets_processed':len(res),'upgraded_total':sum(1 for r in res if r['upgraded']=='yes'),'result_tier_counts':tier,'upgraded_tier_counts':up,'final_db_tier_counts':counts(),'important':'Only sale-source/document/visual-boundary evidence can upgrade records. Official parcel system is not proof. Normal photos alone are not proof.'}
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\upgrade_candidate_confidence_and_lengths.py:108: "menu_display_assumption": "If the parcel/listing menu displays verification_note/source polygon fields, it will show area/perimeter/sides after this apply. If not, frontend must read these fields.",
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\upgrade_candidate_confidence_and_lengths.py:169: (exports / "ESTIMATED_CANDIDATE_confidence_upgrade_dashboard.html").write_text(make_html(summary, review_rows), encoding="utf-8")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\upgrade_d_tier_sale_geometry_confidence.py:145: note=f"D_TIER_DEEP_MEDIA_UPGRADE | old={old_tier}/{old_score} | new={cls['new_confidence_tier']}/{new_score} | source_area={cls['source_area']} | plan_signal={cls['plan_signal']} | public_doc={cls['public_doc_downloaded']} | reference={cls['reference_signal']} | polygon_signal={cls['polygon_signal']} | area_hits={cls['area_hits']} | evidence_links={cls['high_value_links_found']} | downloads={cls['downloaded_count']} | Normal photos alone are not treated as geometry proof. Official parcel system is not proof. Non-A rows remain estimated sale-geometry candidates."
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\upgrade_d_tier_sale_geometry_confidence.py:153: summary={'finished_at':dt.datetime.now(dt.timezone.utc).isoformat(),'input_d_rows_processed':len(results),'upgraded_total':sum(1 for r in results if r['upgraded']=='yes'),'result_tier_counts_for_processed_rows':counts,'upgraded_tier_counts':upgraded_counts,'important':'D rows are upgraded only if sale-source evidence improves. Normal photos alone do not prove geometry. Official parcel system is not proof.'}
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\match\parcel_matcher.py:15: ListingParcelLink,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\match\parcel_matcher.py:20: ParcelInspire,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\match\parcel_matcher.py:43: 'name_attrs': ['parcel_name'],
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\match\parcel_matcher.py:88: 'name_attrs': ['parcel_name', 'title', 'address_text'],
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\match\parcel_matcher.py:95: parcel_id: int
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\publish\parcel_signal_summary.py:12: ListingParcelLink,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\publish\parcel_signal_summary.py:16: ParcelInspire,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\publish\parcel_signal_summary.py:17: ParcelSignalSummary,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\publish\parcel_signal_summary.py:60: def _build_official_landhub_record(link: ListingParcelLink, record: ListingsLandHub | None) -> dict[str, Any]:
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\publish\parcel_signal_summary.py:78: "parcel_name": getattr(record, "parcel_name", None),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\government_property_finder.py:98: "export_manifest": {
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\hmlr_inspire.py:24: sample_filename = 'hmlr_inspire_parcels.json'
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\hmlr_inspire.py:258: parcel_ref = self._pick_parcel_ref(row)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\hmlr_inspire.py:259: if not parcel_ref:
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\hmlr_inspire.py:261: inspire_id = self._build_canonical_inspire_id(authority, parcel_ref)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\hmlr_inspire.py:268: 'parcel_ref': parcel_ref,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\homes_england_landhub.py:122: 'parcel_name': pick_first(
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\homes_england_landhub.py:124: 'parcel_name',
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\homes_england_landhub.py:125: 'parcelName',
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\homes_england_landhub.py:126: 'ParcelName',
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\homes_england_landhub.py:127: 'Parcel_Name',
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\market\vendor_feed.py:103: matched_parcel_ref = get_mapped_value(row, field_mapping, "matched_parcel_ref", "parcel_ref")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\market\vendor_feed.py:125: "parcel_name": get_mapped_value(row, field_mapping, "parcel_name", "site_name"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\market\vendor_feed.py:141: "matched_parcel_ref": matched_parcel_ref,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\city_vector_service.py:55: FROM parcel_future_growth_scores s
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\city_vector_service.py:56: JOIN parcels_inspire p ON p.parcel_id = s.parcel_id
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\city_vector_service.py:62: count(*) AS parcel_count,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\city_vector_service.py:86: min_parcels = int(self.settings.future_growth_vector_min_parcels)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\city_vector_service.py:91: parcel_count = int(row.get("parcel_count") or 0)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\cli.py:36: parser.add_argument("--parcel-ids", nargs="*", default=None)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\cli.py:43: parcel_ids = [int(value) for value in (args.parcel_ids or []) if str(value).strip()]
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\cli.py:50: parcel_ids=parcel_ids or None,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\constants.py:29: "INTERSECTS_PARCEL": 1.0,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\constants.py:41: "PARCEL": 100.0,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\constants.py:66: PARCEL_GEOGRAPHY_WARNING = "Bu veri parsel ozelinde degil, bagli local authority duzeyinde kullanilmistir."
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\evidence_service.py:11: from app.future_growth.constants import PARCEL_GEOGRAPHY_WARNING
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\evidence_service.py:15: "INTERSECTS_PARCEL": "Parsel ile kesisiyor",
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\evidence_service.py:32: def get_latest_score(self, parcel_id: int) -> dict[str, Any]:
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\evidence_service.py:38: s.parcel_id,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\evidence_service.py:56: FROM parcel_future_growth_scores s
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\jobs.py:22: parcel_ids: list[int] | None = None,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\jobs.py:30: parcel_ids=parcel_ids,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\scoring_service.py:11: from app.db.models import CityGrowthVector, ParcelFutureGrowthEvidence, ParcelFutureGrowthScore
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\scoring_service.py:29: "bus_route_density": ("transport", 14.0),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\scoring_service.py:52: parcel_ids: list[int] | None = None,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\scoring_service.py:60: max_batch = int(limit or self.settings.future_growth_max_parcel_batch)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\scoring_service.py:61: parcels = self._load_target_parcels(
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\scoring_utils.py:22: return "INTERSECTS_PARCEL"
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\scoring_utils.py:137: has_parcel_like_evidence = any((_geography_cap(row.get("geography_level")) >= 90.0) for row in evidence_rows)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\scoring_utils.py:138: if not has_parcel_like_evidence:
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\tile_service.py:78: p.parcel_id,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\tile_service.py:92: FROM parcel_future_growth_scores s
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\tile_service.py:93: JOIN parcels_inspire p ON p.parcel_id = s.parcel_id
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\tile_service.py:95: ORDER BY s.future_growth_percent DESC, s.confidence_score DESC, p.parcel_id ASC
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\future_growth\tile_service.py:124: "parcel_id": row["parcel_id"],
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\middleware\map_listings_cache.py:17: if request.method != "GET" or request.url.path not in {"/map/listings", "/map/parcels"}:
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\schemas\admin.py:14: expected_parcel_authorities: int
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\schemas\admin.py:15: loaded_parcel_authorities: int
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\schemas\admin.py:16: parcel_count: int
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\schemas\admin.py:18: parcel_signal_summary_count: int
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\schemas\admin.py:19: official_sale_signal_parcels: int
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\schemas\contractor.py:8: class ContractorExportRowsResponse(BaseModel):
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\schemas\contractor.py:16: class ContractorStatusResponse(BaseModel):
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\schemas\contractor.py:24: parcel_match_manifest: dict[str, Any] = Field(default_factory=dict)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\schemas\contractor.py:25: export_manifest: dict[str, Any] = Field(default_factory=dict)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\schemas\contractor.py:28: class ContractorParcelContactsResponse(BaseModel):
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\schemas\cost.py:49: parcel_id: int = Field(ge=1)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\schemas\cost.py:92: contractor_ohp: float
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\schemas\cost.py:107: parcel_id: int
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\schemas\cost.py:125: class ParcelCostEstimateHistoryItem(BaseModel):
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\schemas\cost.py:127: parcel_id: int
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\schemas\facility.py:28: class ParcelContextMetricDetailItem(BaseModel):
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\schemas\facility.py:34: touches_parcel: bool = False
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\schemas\facility.py:39: class ParcelContextSummaryItem(BaseModel):
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\schemas\facility.py:40: parcel_id: int
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\schemas\facility.py:41: parcel_ref: str
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\schemas\future_growth.py:10: parcel_id: int
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\schemas\future_growth.py:30: parcel_id: int
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\schemas\future_growth.py:50: class FutureGrowthParcelDetailResponse(BaseModel):
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\schemas\future_growth.py:51: parcel_id: int
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\schemas\future_growth.py:100: parcel_ids: list[int] | None = None
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\schemas\listing.py:14: parcel_name: str | None = None
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\schemas\listing.py:26: matched_parcel_id: int | None = None
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\schemas\listing.py:27: matched_parcel_ref: str | None = None
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\schemas\listing.py:44: parcel_match_status: str | None = None
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\schemas\ops.py:18: contractor_preflight_path: str
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\schemas\parcel.py:10: from app.schemas.facility import ParcelContextSummaryItem, ParcelScenarioScoreItem
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\schemas\parcel.py:11: from app.schemas.planned_asset import ParcelPlannedFeatureSummary
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\schemas\parcel.py:14: class ParcelListItem(BaseModel):
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\schemas\parcel.py:50: parcel_id: int
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\schemas\parcel.py:52: parcel_ref: str
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\schemas\planned_asset.py:81: class ParcelPlannedFeatureSummary(BaseModel):
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\schemas\planned_asset.py:82: parcel_id: int
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\schemas\planned_asset.py:115: class ParcelFutureGrowthScoreResponse(BaseModel):
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\schemas\planned_asset.py:116: parcel_id: int
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\schemas\planned_asset.py:125: summary: ParcelPlannedFeatureSummary
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\admin_publish_service.py:8: ParcelLinkingRebuildRequest,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\admin_publish_service.py:10: from app.services.parcel_linking_service import rebuild_parcel_links_and_signals
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\admin_publish_service.py:20: parcel_linking = rebuild_parcel_links_and_signals(
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\admin_publish_service.py:22: ParcelLinkingRebuildRequest(
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\admin_publish_service.py:32: parcel_linking=parcel_linking,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\admin_service.py:14: ListingParcelLink,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\admin_service.py:18: ParcelInspire,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\admin_service.py:19: ParcelSignalSummary,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\admin_service.py:130: message=f"{label} manifest is present but no active live export file is ready yet, so this source cannot grow visible sale-ready parcels.",
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\admin_service.py:143: expected_parcel_authorities = len(manifest_records)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\cost_engine_service.py:23: ParcelCostEstimate,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\cost_engine_service.py:24: ParcelCostMaterialLine,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\cost_engine_service.py:25: ParcelInspire,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\cost_engine_service.py:40: Cost50ParcelsSummary,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\cost_engine_service.py:52: ParcelCostEstimateHistoryItem,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\facility_service.py:17: ParcelContextMetricDetail,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\facility_service.py:18: ParcelContextSummary,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\facility_service.py:19: ParcelInspire,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\facility_service.py:20: ParcelScenarioScore,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\facility_service.py:25: ParcelContextMetricDetailItem,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\listing_service.py:12: ListingParcelLink,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\listing_service.py:16: ParcelInspire,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\listing_service.py:52: has_parcel_match = bool(matched.get("matched_parcel_ref") or matched.get("matched_inspire_id"))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\listing_service.py:58: elif has_parcel_match:
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\listing_service.py:59: status = "derived_from_parcel_match"
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\managed_sales_repository.py:70: "parcel_name": row.get("parcel_name"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\managed_sales_repository.py:73: "parcel_ref": row.get("parcel_ref"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\managed_sales_repository.py:102: "parcel_name": row.parcel_name,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\managed_sales_repository.py:105: "parcel_ref": row.parcel_ref,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\managed_sales_repository.py:136: parcel_ref: str | None = None,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\parcel_linking_service.py:10: ListingParcelLink,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\parcel_linking_service.py:14: ParcelSignalSummary,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\parcel_linking_service.py:19: from app.etl.match.parcel_matcher import match_source_records
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\parcel_linking_service.py:20: from app.etl.publish.parcel_signal_summary import refresh_parcel_signal_summary
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\parcel_linking_service.py:22: ParcelLinkingRebuildRequest,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\parcel_service.py:15: ParcelContextSummary,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\parcel_service.py:16: ListingParcelLink,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\parcel_service.py:20: ParcelInspire,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\parcel_service.py:21: ParcelSignalSummary,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\parcel_service.py:27: from app.schemas.parcel import ParcelDetail, ParcelHistoryItem, ParcelListItem, ParcelSignalItem
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\parcel_use_classifier.py:7: PARCEL_USE_LABELS = ("residential", "retail", "office", "industrial", "mixed_use")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\parcel_use_classifier.py:81: def classify_parcel_use(
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\parcel_use_classifier.py:112: scores: dict[str, float] = {label: 0.0 for label in PARCEL_USE_LABELS}
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\parcel_use_classifier.py:113: factors_by_label: dict[str, list[dict[str, Any]]] = {label: [] for label in PARCEL_USE_LABELS}
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\planned_asset_service.py:15: ParcelInspire,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\planned_asset_service.py:16: ParcelPlannedAssetMatch,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\planned_asset_service.py:25: ParcelFutureGrowthScoreResponse,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\planned_asset_service.py:26: ParcelPlannedFeatureSummary,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\planned_asset_service.py:345: def match_to_parcels(session: Session, *, asset_ids: list[int] | None = None) -> tuple[int, set[int]]:
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\runtime_ops_service.py:88: contractor_preflight_path=_registry_value(
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\runtime_ops_service.py:90: "contractor_preflight_path",
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\runtime_ops_service.py:91: str(settings.contractor_preflight_audit_path),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\runtime_ops_service.py:122: and status.accuracy.parcel_match_accuracy.current is not None
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\runtime_ops_service.py:132: _path_check("contractor_preflight_path", registry.contractor_preflight_path),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\sale_land_verification.py:12: L2_MATCHED_OFFICIAL_PARCEL = "L2_matched_official_parcel"
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\sale_land_verification.py:101: if _has_value(record, "inspire_id", "title_number", "official_parcel_id", "matched_parcel_id"):
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\sale_land_verification.py:103: level = VerificationLevel.L2_MATCHED_OFFICIAL_PARCEL
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\source_catalog.py:9: 'category': 'parcel_backbone',
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\source_catalog.py:11: 'description': 'Indicative parcel geometry backbone.',
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\source_catalog.py:67: 'description': 'Official education facilities feed for parcel context scoring.',
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\supabase_admin_service.py:44: def list_supabase_parcel_records(session: Session, parcel_ref: str, *, limit: int = 20) -> list[SupabaseLandListingRecord]:
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\supabase_admin_service.py:45: parcel_key = (parcel_ref or "").strip()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\supabase_admin_service.py:46: if not parcel_key:
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\supabase_admin_service.py:50: parcel_ref=parcel_key,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\supabase_admin_service.py:122: def list_supabase_parcel_records(session=None, parcel_ref=None, *, limit=500):
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\supabase_sync_service.py:34: or candidate.parcel_ref
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\supabase_sync_service.py:50: or candidate.parcel_ref
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\supabase_sync_service.py:53: listing_title = candidate.listing_title or candidate.site_name or candidate.parcel_name or candidate.parcel_ref or candidate.inspire_id or candidate.id
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\supabase_sync_service.py:61: "parcel_name": candidate.parcel_name,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\supabase_sync_service.py:64: "parcel_ref": candidate.parcel_ref,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\warnings.py:4: {'code': 'brownfield_not_for_sale', 'message': 'Brownfield does not guarantee a parcel is currently for sale.'},
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\scripts\contractor_collect_companies_house.py:3: AAYS/TerraYield UK contractor intelligence - Companies House collector.
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\scripts\contractor_collect_companies_house.py:28: DEFAULT_STORAGE_ROOT = r"E:\AAYS_DATA\contractor"
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\scripts\contractor_collect_companies_house.py:34: "contractor",
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\scripts\contractor_collect_companies_house.py:35: "construction contractor",
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\scripts\contractor_collect_companies_house.py:36: "civil engineering contractor",
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\scripts\contractor_collect_procurement_ocds.py:3: AAYS/TerraYield UK contractor intelligence - Procurement OCDS collector.
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\scripts\contractor_collect_procurement_ocds.py:31: DEFAULT_STORAGE_ROOT = r"E:\AAYS_DATA\contractor"
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\scripts\contractor_collect_procurement_ocds.py:106: req_headers = {"Accept": "application/json", "User-Agent": "AAYS-TerraYield/contractor-intelligence"}
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\scripts\contractor_collect_procurement_ocds.py:237: resp = session.get(ons_lookup_url, headers={"User-Agent": "AAYS-TerraYield/contractor-intelligence"}, timeout=120)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\scripts\contractor_collect_procurement_ocds.py:319: parser = argparse.ArgumentParser(description="Collect official UK procurement OCDS snapshots for contractor intelligence.")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\scripts\contractor_env.py:2: """Safe contractor DB environment loading utilities."""
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\scripts\contractor_env.py:11: BRIDGE_LOCAL_SECRET_PATH = Path(r"C:\AAYS1_GITHUB_BRIDGE\local-secrets\contractor-db.env")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\scripts\contractor_env.py:35: contractor_url = source.get("CONTRACTOR_DATABASE_URL")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\scripts\contractor_env.py:36: if contractor_url and not target.get("DATABASE_URL"):
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\scripts\contractor_env.py:37: target["DATABASE_URL"] = contractor_url
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\scripts\contractor_export_for_app.py:2: """Export contractor intelligence for app consumption with DO_NOT_CONTACT controls."""
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\scripts\contractor_export_for_app.py:14: from contractor_env import load_contractor_env
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\scripts\contractor_export_for_app.py:16: DEFAULT_STORAGE_ROOT = r"E:\AAYS_DATA\contractor"
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\scripts\contractor_export_for_app.py:60: parser = argparse.ArgumentParser(description="Export app-ready contractor intelligence snapshots.")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\scripts\contractor_export_for_app.py:65: env_info = load_contractor_env(Path(args.project_root))
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\scripts\contractor_load_to_postgres.py:2: """Load curated contractor intelligence snapshots to PostgreSQL/PostGIS."""
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\scripts\contractor_load_to_postgres.py:19: from contractor_env import load_contractor_env, redact_secrets
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\scripts\contractor_load_to_postgres.py:21: DEFAULT_STORAGE_ROOT = r"E:\AAYS_DATA\contractor"
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\scripts\contractor_load_to_postgres.py:57: create table if not exists contractor_company (
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\scripts\contractor_load_to_postgres.py:58: contractor_id text primary key,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\scripts\contractor_match_to_parcels.py:2: """Match contractors to parcels using fail-closed, evidence-aware hierarchy.
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\scripts\contractor_match_to_parcels.py:26: from contractor_env import load_contractor_env, redact_secrets
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\scripts\contractor_match_to_parcels.py:28: DEFAULT_STORAGE_ROOT = r"E:\AAYS_DATA\contractor"
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\scripts\contractor_match_to_parcels.py:49: path = storage_root / "raw" / "status" / f"{status_type}_parcel_match.json"
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\scripts\contractor_match_to_parcels.py:50: write_json(path, {"status": status_type, "source_name": "contractor parcel matcher", "reason": reason, "details": details or {}, "fetched_at": utc_now(), "license_name": None})
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\scripts\contractor_normalize_and_score.py:3: Normalize official UK contractor signals and compute conservative scores.
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\scripts\contractor_normalize_and_score.py:11: - curated/contractor_score_snapshot.csv
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\scripts\contractor_normalize_and_score.py:12: - curated/contractor_score_snapshot.jsonl
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\scripts\contractor_normalize_and_score.py:13: - curated/contractor_project_snapshot.csv
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\scripts\contractor_normalize_and_score.py:32: DEFAULT_STORAGE_ROOT = r"E:\AAYS_DATA\contractor"
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\scripts\contractor_pipeline.py:2: """CC50 contractor pipeline.
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\scripts\contractor_pipeline.py:31: "parcel_id", "structure_type", "contractor_id", "company_name", "contact_status", "do_not_contact",
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\scripts\contractor_pipeline.py:306: def add_provenance(rows: List[Dict[str, Any]], contractor_id: str, source_key: str, source_url: Optional[str], record_id: Optional[str], field: str, value: Any, fetched_at: str) -> None:
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\scripts\contractor_pipeline.py:309: "entity_id": contractor_id,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\scripts\contractor_pipeline.py:310: "entity_type": "contractor",
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\scripts\future_growth_frontend_smoke.py:69: detail_path_template = str(config.get("api", {}).get("parcelDetail") or "/api/future-growth/parcels/{parcelId}")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\scripts\future_growth_frontend_smoke.py:88: required_layer_props = {"parcel_id", "future_growth_percent", "confidence_score", "color_class", "hex_color"}
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\scripts\future_growth_frontend_smoke.py:92: parcel_id = props.get("parcel_id")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\scripts\future_growth_frontend_smoke.py:95: parcel_id = None
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\scripts\future_growth_frontend_smoke.py:100: if parcel_id is not None:
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\scripts\README_CONTRACTOR_PIPELINE.md:1: # AAYS/TerraYield Contractor Intelligence Pipeline
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\scripts\README_CONTRACTOR_PIPELINE.md:3: Bu script seti Ingiltere contractor intelligence icin yalnizca resmi/structured kaynaklari kullanir:
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\scripts\README_CONTRACTOR_PIPELINE.md:22: `E:\AAYS_DATA\contractor`
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\scripts\README_CONTRACTOR_PIPELINE.md:45: `E:\AAYS_DATA\contractor\raw\status\blocked_by_missing_credential_companies_house_public_data_api.json`
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\scripts\README_CONTRACTOR_PIPELINE.md:50: $env:CONTRACTOR_DATABASE_URL="postgresql://postgres:postgres@localhost:55460/terrayield_land"

## Next Action
Patch app code to read contractor export files or expose them through a route.
