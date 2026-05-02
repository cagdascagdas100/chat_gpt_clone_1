# ChatGPT Runner Result

## Task
TerraYield sales-history status timeout diagnosis

## Task ID
terrayield-status-timeout-diagnose-001

## Progress
84%

## Time
05/02/2026 23:57:45

## Working Directory
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence

## Exit Code
0

## Command
Write-Output 'TASK: /map/sales-history/status timeout tanilama'; Write-Output 'PROGRESS: 84%'; Write-Output 'ESTIMATED_WAIT: 3-5 dakika'; Write-Output 'START_TIME:'; Get-Date; Write-Output '--- ROUTE SEARCH status ---'; Get-ChildItem app -Recurse -File -Include *.py -ErrorAction SilentlyContinue | Select-String -Pattern 'sales-history/status|sales_history/status|status' -CaseSensitive:$false | Select-Object -First 120 | ForEach-Object { $_.Path + ':' + $_.LineNumber + ': ' + $_.Line }; Write-Output '--- DOCKER PS ---'; docker compose ps 2>&1; Write-Output '--- STATUS ENDPOINT 10 SEC ---'; try { $sw=[System.Diagnostics.Stopwatch]::StartNew(); $r=Invoke-WebRequest -Uri 'http://localhost:8010/map/sales-history/status' -UseBasicParsing -TimeoutSec 10; $sw.Stop(); Write-Output ('OK status=' + [string]$r.StatusCode + ' ms=' + [string]$sw.ElapsedMilliseconds + ' bytes=' + [string]$r.Content.Length); Write-Output ($r.Content.Substring(0,[Math]::Min(1000,$r.Content.Length))) } catch { $sw.Stop(); Write-Output ('FAIL ms=' + [string]$sw.ElapsedMilliseconds + ' error=' + $_.Exception.Message) }; Write-Output '--- STATUS ENDPOINT 45 SEC ---'; try { $sw=[System.Diagnostics.Stopwatch]::StartNew(); $r=Invoke-WebRequest -Uri 'http://localhost:8010/map/sales-history/status' -UseBasicParsing -TimeoutSec 45; $sw.Stop(); Write-Output ('OK status=' + [string]$r.StatusCode + ' ms=' + [string]$sw.ElapsedMilliseconds + ' bytes=' + [string]$r.Content.Length); Write-Output ($r.Content.Substring(0,[Math]::Min(1000,$r.Content.Length))) } catch { $sw.Stop(); Write-Output ('FAIL ms=' + [string]$sw.ElapsedMilliseconds + ' error=' + $_.Exception.Message) }; Write-Output '--- API LOGS TAIL STATUS RELATED ---'; docker logs --tail 250 terrayield_land_api 2>&1 | Select-String -Pattern 'sales-history/status|timeout|error|exception|traceback|status' -CaseSensitive:$false | Select-Object -Last 120 | ForEach-Object { $_.Line }; Write-Output 'END_TIME:'; Get-Date; Write-Output 'STATUS_TIMEOUT_DIAGNOSE_DONE'

## Output
TASK: /map/sales-history/status timeout tanilama
PROGRESS: 84%
ESTIMATED_WAIT: 3-5 dakika
START_TIME:

2 Mayıs 2026 Cumartesi 23:56:48
--- ROUTE SEARCH status ---
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\aays_sales_history_layers.py:117:         raise HTTPException(status_code=500, detail=f"AAYS sales query failed: {exc}") from exc
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\aays_sales_history_layers.py:126: @router.get("/map/sales-history/status")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\aays_sales_history_layers.py:127: def status():
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\aays_sales_history_layers.py:560:             status_code=404,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\aays_sales_history_layers.py:567:             status_code=500,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\aays_sales_history_layers.py:572: @router.get("/map/sales-history/l4-reviewed-package/status")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\aays_sales_history_layers.py:573: def aays68_l4_reviewed_package_status() -> _aays68_Dict[str, _aays68_Any]:
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\aays_sales_history_layers.py:577:         "status": "ok",
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\aays_sales_history_layers.py:614:         "status": "ok",
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\admin.py:13:     ParcelLinkingStatus,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\admin.py:19:     SupabaseSyncStatus,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\admin.py:23: from app.services.parcel_linking_service import get_parcel_linking_status, rebuild_parcel_links_and_signals
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\admin.py:30: from app.services.supabase_sync_service import get_supabase_sync_status, sync_seed_candidates_to_supabase
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\admin.py:44:     listing_status: str | None = None,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\admin.py:53:         listing_status=listing_status,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\admin.py:62: @router.get("/supabase/status", response_model=SupabaseSyncStatus)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\admin.py:63: def get_admin_supabase_status() -> SupabaseSyncStatus:
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\admin.py:64:     return get_supabase_sync_status()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\admin.py:70:     listing_status: str | None = None,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\admin.py:76:         listing_status=listing_status,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\admin.py:87:         raise HTTPException(status_code=400, detail=str(exc)) from exc
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\admin.py:95:         raise HTTPException(status_code=400, detail=str(exc)) from exc
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\admin.py:103:         raise HTTPException(status_code=400, detail=str(exc)) from exc
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\admin.py:121: @router.get("/parcel-linking/status", response_model=ParcelLinkingStatus)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\admin.py:122: def get_admin_parcel_linking_status(db: DBSession) -> ParcelLinkingStatus:
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\admin.py:123:     return get_parcel_linking_status(db)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\brownfield.py:26:     planning_status: str | None = None,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\brownfield.py:35:     items, _ = list_brownfield_sites(db, source=source, local_authority=authority, planning_status=planning_status, min_confidence=min_confidence, max_confidence=max_confidence, bbox=_parse_bbox(bbox), limit=limit, offset=offset)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\health.py:16:     database_status = 'ok'
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\health.py:20:         database_status = 'degraded'
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\health.py:24:         database=database_status,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\listings.py:29:     listing_status: str | None = None,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\listings.py:46:         listing_status=listing_status,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\map_layers.py:75:     listing_status: str | None = None,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\map_layers.py:91:         listing_status=listing_status,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\map_layers.py:110:     planning_status: str | None = None,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\map_layers.py:118:     items, _ = list_brownfield_sites(db, source=source, local_authority=authority, planning_status=planning_status, min_confidence=min_confidence, max_confidence=max_confidence, bbox=_parse_bbox(bbox), limit=limit, offset=offset)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\proxy.py:104:         if upstream_response.status_code in {200, 206, 204, 304, 416}:
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\proxy.py:108:             if request.method == "HEAD" or upstream_response.status_code in {204, 304, 416}:
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\proxy.py:110:                     status_code=upstream_response.status_code,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\proxy.py:117:                 status_code=upstream_response.status_code,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\proxy.py:123:         last_error = f"{target_url}: upstream {upstream_response.status_code}"
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\proxy.py:127:     raise HTTPException(status_code=502, detail=f"Parcel proxy upstream hatasi: {last_error or 'unknown error'}")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\sources.py:6: from app.schemas.common import SourceDescriptor, SourceStatus
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\sources.py:7: from app.services.source_service import list_source_descriptors, list_source_statuses
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\sources.py:17: @router.get('/status', response_model=list[SourceStatus])
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\sources.py:18: def get_source_statuses(db: DBSession) -> list[SourceStatus]:
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\sources.py:19:     return list_source_statuses(db)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\cli\print_storage_status.py:22:     print("TerraYield storage status")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\cli\run_storage_state_sync_loop.py:23:     status_path = local_root / "storage_sync" / "backfill_state.json"
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\cli\run_storage_state_sync_loop.py:29:             _write_status(status_path, local_root, external_root, "completed_max_iterations", {"iterations": iterations})
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\cli\run_storage_state_sync_loop.py:39:         _write_status(status_path, local_root, external_root, "running", payload)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\cli\run_storage_state_sync_loop.py:45: def _write_status(
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\cli\run_storage_state_sync_loop.py:46:     status_path: Path,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\cli\run_storage_state_sync_loop.py:49:     status: str,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\cli\run_storage_state_sync_loop.py:52:     status_path.parent.mkdir(parents=True, exist_ok=True)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\cli\run_storage_state_sync_loop.py:55:         "status": status,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\cli\run_storage_state_sync_loop.py:60:     status_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\clients\supabase_rest.py:64:             response.raise_for_status()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\clients\supabase_rest.py:80:             response.raise_for_status()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\clients\supabase_rest.py:91:             response.raise_for_status()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\db\models.py:65:     marketing_status: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\db\models.py:68:     planning_status: Mapped[str | None] = mapped_column(String(255), nullable=True)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\db\models.py:86:     ownership_status: Mapped[str | None] = mapped_column(String(255), nullable=True)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\db\models.py:87:     planning_permission_status: Mapped[str | None] = mapped_column(String(255), nullable=True)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\db\models.py:111:     ownership_status: Mapped[str | None] = mapped_column(String(255), nullable=True)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\db\models.py:112:     planning_status: Mapped[str | None] = mapped_column(String(255), nullable=True)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\db\models.py:149:     listing_status: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\db\models.py:173:     listing_status: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\db\models.py:274:     status: Mapped[str] = mapped_column(String(50), nullable=False, default="queued", index=True)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\db\models.py:293:     official_sale_status: Mapped[str | None] = mapped_column(String(64), nullable=True)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\db\models.py:341:     status: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\db\models.py:366:     status: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\publish\parcel_signal_summary.py:79:         "listing_status": getattr(record, "marketing_status", None),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\publish\parcel_signal_summary.py:82:         "planning_status": getattr(record, "planning_status", None),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\publish\parcel_signal_summary.py:116:         "listing_status": getattr(record, "listing_status", None),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\publish\parcel_signal_summary.py:157:         "listing_status": getattr(record, "listing_status", None),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\publish\parcel_signal_summary.py:192:         "planning_status": getattr(record, "planning_permission_status", None) or getattr(record, "planning_status", None),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\publish\parcel_signal_summary.py:193:         "ownership_status": getattr(record, "ownership_status", None),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\publish\parcel_signal_summary.py:260:         official_sale_status = None
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\publish\parcel_signal_summary.py:281:                 if source_name in {"homes_england_landhub", "government_property_finder"} and official_sale_status is None:
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\publish\parcel_signal_summary.py:282:                     official_sale_status = getattr(first_record, "marketing_status", None) or getattr(first_record, "listing_status", None)
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\publish\parcel_signal_summary.py:364:             "official_sale_status": official_sale_status,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\publish\parcel_signal_summary.py:403:             official_sale_status=official_sale_status,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\facilities\base.py:371:                     "status": get_mapped_value(props, field_mapping, "status"),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\market\vendor_feed.py:7: from app.etl.sources.manual_listing_exports import get_mapped_value, load_export_rows, normalize_status
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\market\vendor_feed.py:50:             status_mapping = manifest.get("status_mapping") or {}
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\market\vendor_feed.py:121:                     "listing_status": normalize_status(get_mapped_value(row, field_mapping, "listing_status", "status"), status_mapping),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\government_property_finder.py:5: from app.etl.sources.manual_listing_exports import get_mapped_value, load_export_rows, normalize_status
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\government_property_finder.py:40:             status_mapping = manifest.get("status_mapping") or {}
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\government_property_finder.py:87:                     "listing_status": normalize_status(get_mapped_value(row, field_mapping, "listing_status", "status"), status_mapping),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\hmlr_inspire.py:117:                     listing_response.raise_for_status()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\hmlr_inspire.py:123:                 response.raise_for_status()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\hmlr_price_paid.py:23:         response.raise_for_status()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\hmlr_price_paid.py:64:                     'record_status': row[15] if len(row) > 15 else None,
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\hmlr_price_paid.py:116:                     'metadata': {'record_status': pick_first(row, 'record_status', 'Record Status - monthly file only')},
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\homes_england_landhub.py:37:                 response.raise_for_status()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\homes_england_landhub.py:88:                 normalized.append({**row, 'marketing_status': self._normalize_status(row.get('marketing_status'))})
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\homes_england_landhub.py:144:                     'marketing_status': self._normalize_status(
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\homes_england_landhub.py:147:                             'marketing_status',
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\homes_england_landhub.py:148:                             'marketingStatus',
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\homes_england_landhub.py:149:                             'MarketingStatus',
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\homes_england_landhub.py:150:                             'Marketing_Status',
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\homes_england_landhub.py:151:                             'status',
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\homes_england_landhub.py:152:                             'Status',
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\homes_england_landhub.py:169:                     'planning_status': pick_first(attrs, 'planning_status', 'planningStatus', 'PlanningStatus', 'Planning_Status'),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\homes_england_landhub.py:182:     def _normalize_status(value: Any) -> str:
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\homes_england_landhub.py:183:         status_raw = (str(value).strip().lower() if value is not None else '')
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\homes_england_landhub.py:184:         if any(token in status_raw for token in ('stc', 'sold subject')):
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\homes_england_landhub.py:186:         if 'market' in status_raw or 'sale' in status_raw or 'available' in status_raw:
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\homes_england_landhub.py:188:         if 'pipeline' in status_raw:
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\homes_england_landhub.py:190:         if 'disposed' in status_raw or 'sold' in status_raw:
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\http_client.py:24:         status_forcelist=(429, 500, 502, 503, 504),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\http_client.py:56:                 response.raise_for_status()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\local_authority_brownfield.py:34:             response.raise_for_status()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\local_authority_brownfield.py:108:                     'ownership_status': pick_first(props, 'OwnershipStatus', 'ownership_status'),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\local_authority_brownfield.py:109:                     'planning_status': pick_first(props, 'PlanningStatus', 'planning_status'),
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\manual_listing_exports.py:63: def normalize_status(value: Any, mapping: dict[str, Any] | None = None) -> str | None:
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\planning_data_brownfield.py:32:                     response.raise_for_status()
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\planning_data_brownfield.py:48:             response.raise_for_status()
--- DOCKER PS ---
NAME                      IMAGE                    COMMAND                  SERVICE   CREATED       STATUS        PORTS
terrayield_land_api       python:3.12-slim         "bash -lc 'pip instaÔÇĞ"   api       9 hours ago   Up 9 hours    0.0.0.0:8010->8010/tcp, [::]:8010->8010/tcp
terrayield_land_postgis   postgis/postgis:16-3.4   "docker-entrypoint.sÔÇĞ"   db        2 days ago    Up 34 hours   0.0.0.0:55460->5432/tcp, [::]:55460->5432/tcp
--- STATUS ENDPOINT 10 SEC ---
FAIL ms=10166 error=The operation has timed out.
--- STATUS ENDPOINT 45 SEC ---
FAIL ms=44996 error=The operation has timed out.
--- API LOGS TAIL STATUS RELATED ---
  File "/usr/local/lib/python3.12/site-packages/starlette/middleware/errors.py", line 186, in __call__
  File "/usr/local/lib/python3.12/site-packages/starlette/middleware/errors.py", line 164, in __call__
  File "/usr/local/lib/python3.12/site-packages/starlette/middleware/exceptions.py", line 63, in __call__
    await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
  File "/usr/local/lib/python3.12/site-packages/starlette/_exception_handler.py", line 53, in wrapped_app
  File "/usr/local/lib/python3.12/site-packages/starlette/_exception_handler.py", line 42, in wrapped_app
    await wrap_app_handling_exceptions(app, request)(scope, receive, send)
  File "/usr/local/lib/python3.12/site-packages/starlette/_exception_handler.py", line 53, in wrapped_app
  File "/usr/local/lib/python3.12/site-packages/starlette/_exception_handler.py", line 42, in wrapped_app
    self._handle_dbapi_exception(
  File "/usr/local/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 2363, in _handle_dbapi_exception
    raise sqlalchemy_exception.with_traceback(exc_info[2]) from e
    raise ex.with_traceback(None)
sqlalchemy.exc.DataError: (psycopg.errors.InvalidParameterValue) Only lon/lat coordinate systems are supported in geography.
INFO:     172.18.0.1:43578 - "GET /map/sales-layers/verified-history?city=London&status=sale_ready HTTP/1.1" 200 OK
INFO:     172.18.0.1:43596 - "GET /map/sales-layers/verified-history?location=London&status=sale_ready HTTP/1.1" 200 OK
INFO:     172.18.0.1:53666 - "GET /map/sales-layers/verified-history?city=London&status=sale_ready&limit=500 HTTP/1.1" 200 OK
INFO:     172.18.0.1:53670 - "GET /map/sales-layers/verified-history?city=London&status=sale_ready&top=500 HTTP/1.1" 200 OK
INFO:     172.18.0.1:53680 - "GET /map/sales-history/status HTTP/1.1" 200 OK
INFO:     172.18.0.1:42572 - "GET /map/sales-history/status?city=London HTTP/1.1" 200 OK
INFO:     172.18.0.1:44444 - "GET /map/sales-history/status?city=London&status=sale_ready HTTP/1.1" 200 OK
INFO:     172.18.0.1:58228 - "GET /map/sales-history/status?city=London&sale_ready=true HTTP/1.1" 200 OK
INFO:     172.18.0.1:41534 - "GET /map/sales-history/status?location=London HTTP/1.1" 200 OK
INFO:     172.18.0.1:49602 - "GET /map/sales-history/status?location=London&status=sale_ready HTTP/1.1" 200 OK
INFO:     172.18.0.1:58306 - "GET /map/sales-history/status?q=London HTTP/1.1" 200 OK
INFO:     172.18.0.1:53474 - "GET /map/sales-history/status?search=London HTTP/1.1" 200 OK
INFO:     172.18.0.1:56520 - "GET /map/sales-history/status?limit=500 HTTP/1.1" 200 OK
INFO:     172.18.0.1:58042 - "GET /map/sales-history/status?city=London&limit=500 HTTP/1.1" 200 OK
INFO:     172.18.0.1:56728 - "GET /map/sales-history/status?city=London&status=sale_ready&limit=500 HTTP/1.1" 200 OK
INFO:     172.18.0.1:52720 - "GET /map/sales-history/status?city=London&top=500 HTTP/1.1" 200 OK
INFO:     172.18.0.1:57062 - "GET /map/sales-history/status?city=London&status=sale_ready&top=500 HTTP/1.1" 200 OK
INFO:     172.18.0.1:45978 - "GET /map/sales-history/external-evidence?city=London&status=sale_ready HTTP/1.1" 200 OK
INFO:     172.18.0.1:46016 - "GET /map/sales-history/external-evidence?location=London&status=sale_ready HTTP/1.1" 200 OK
INFO:     172.18.0.1:46042 - "GET /map/sales-history/external-evidence?city=London&status=sale_ready&limit=500 HTTP/1.1" 200 OK
INFO:     172.18.0.1:55074 - "GET /map/sales-history/external-evidence?city=London&status=sale_ready&top=500 HTTP/1.1" 200 OK
(Background on this error at: https://sqlalche.me/e/20/9h9h)
INFO:     172.18.0.1:55102 - "GET /map/sales-history/parcels?city=London&status=sale_ready HTTP/1.1" 200 OK
INFO:     172.18.0.1:55138 - "GET /map/sales-history/parcels?location=London&status=sale_ready HTTP/1.1" 200 OK
INFO:     172.18.0.1:55176 - "GET /map/sales-history/parcels?city=London&status=sale_ready&limit=500 HTTP/1.1" 200 OK
INFO:     172.18.0.1:55188 - "GET /map/sales-history/parcels?city=London&status=sale_ready&top=500 HTTP/1.1" 200 OK
INFO:     172.18.0.1:55224 - "GET /map/sales-history/combined?city=London&status=sale_ready HTTP/1.1" 200 OK
INFO:     172.18.0.1:55258 - "GET /map/sales-history/combined?location=London&status=sale_ready HTTP/1.1" 200 OK
INFO:     172.18.0.1:36904 - "GET /map/sales-history/combined?city=London&status=sale_ready&limit=500 HTTP/1.1" 200 OK
INFO:     172.18.0.1:36916 - "GET /map/sales-history/combined?city=London&status=sale_ready&top=500 HTTP/1.1" 200 OK
INFO:     172.18.0.1:36926 - "GET /map/sales-history/l4-reviewed-package/status HTTP/1.1" 404 Not Found
INFO:     172.18.0.1:36928 - "GET /map/sales-history/l4-reviewed-package/status?city=London HTTP/1.1" 404 Not Found
INFO:     172.18.0.1:36944 - "GET /map/sales-history/l4-reviewed-package/status?city=London&status=sale_ready HTTP/1.1" 404 Not Found
INFO:     172.18.0.1:36960 - "GET /map/sales-history/l4-reviewed-package/status?city=London&sale_ready=true HTTP/1.1" 404 Not Found
INFO:     172.18.0.1:36974 - "GET /map/sales-history/l4-reviewed-package/status?location=London HTTP/1.1" 404 Not Found
INFO:     172.18.0.1:36980 - "GET /map/sales-history/l4-reviewed-package/status?location=London&status=sale_ready HTTP/1.1" 404 Not Found
INFO:     172.18.0.1:36982 - "GET /map/sales-history/l4-reviewed-package/status?q=London HTTP/1.1" 404 Not Found
INFO:     172.18.0.1:36992 - "GET /map/sales-history/l4-reviewed-package/status?search=London HTTP/1.1" 404 Not Found
INFO:     172.18.0.1:37002 - "GET /map/sales-history/l4-reviewed-package/status?limit=500 HTTP/1.1" 404 Not Found
INFO:     172.18.0.1:37012 - "GET /map/sales-history/l4-reviewed-package/status?city=London&limit=500 HTTP/1.1" 404 Not Found
INFO:     172.18.0.1:37016 - "GET /map/sales-history/l4-reviewed-package/status?city=London&status=sale_ready&limit=500 HTTP/1.1" 404 Not Found
INFO:     172.18.0.1:37024 - "GET /map/sales-history/l4-reviewed-package/status?city=London&top=500 HTTP/1.1" 404 Not Found
INFO:     172.18.0.1:37038 - "GET /map/sales-history/l4-reviewed-package/status?city=London&status=sale_ready&top=500 HTTP/1.1" 404 Not Found
INFO:     172.18.0.1:37062 - "GET /map/sales-history/l4-reviewed-package?city=London&status=sale_ready HTTP/1.1" 404 Not Found
INFO:     172.18.0.1:37084 - "GET /map/sales-history/l4-reviewed-package?location=London&status=sale_ready HTTP/1.1" 404 Not Found
INFO:     172.18.0.1:37136 - "GET /map/sales-history/l4-reviewed-package?city=London&status=sale_ready&limit=500 HTTP/1.1" 404 Not Found
INFO:     172.18.0.1:37156 - "GET /map/sales-history/l4-reviewed-package?city=London&status=sale_ready&top=500 HTTP/1.1" 404 Not Found
END_TIME:
2 Mayıs 2026 Cumartesi 23:57:45
STATUS_TIMEOUT_DIAGNOSE_DONE



