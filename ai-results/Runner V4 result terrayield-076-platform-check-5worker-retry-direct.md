# Runner V4 result terrayield-076-platform-check-5worker-retry-direct  PROJECT=terrayield DISPLAY_PROJECT=TerraYield CHATGPT_PAGE_PROJECT=aays1 TASK=terrayield-076-platform-check-5worker-retry-direct EXIT_CODE=0 RUN_LOG=C:\Users\cagda\Documents\chat_gpt_clone_1\ai-runner-logs\terrayield-076-direct-20260506_162451.log TIME=2026-05-06T16:25:25 
LATEST_RUN_DIR=C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\.aays_real_runs\terrayield__071_platform_finish_5worker_safe__20260506_162453

## C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\.aays_real_runs\terrayield__071_platform_finish_5worker_safe__20260506_162453\terrayield__071_scorecard.csv
```text
metric,score
workers,5
completed_slots,
5
blocked_slots,
0
timeout_slots,
0
program_completion,
75
platform_readiness,78

```
## C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\.aays_real_runs\terrayield__071_platform_finish_5worker_safe__20260506_162453\terrayield__071_status.txt
```text
PROJECT=terrayield
DISPLAY_PROJECT=TerraYield
TASK=
terrayield-071-platform-finish-5worker-safe
WORKERS=5
COMPLETED_SLOTS=
5
BLOCKED_SLOTS=
0
TIMEOUT_SLOTS=
0
PROGRAM_COMPLETION=
75
/100
PLATFORM_READINESS=78/100
NEXT_ACTION=devam et

```
## C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\.aays_real_runs\terrayield__071_platform_finish_5worker_safe__20260506_162453\terrayield__071_summary.md
```text
PROJECT=terrayield
DISPLAY_PROJECT=TerraYield
CHATGPT_PAGE_PROJECT=aays1
TASK=terrayield-071-platform-finish-5worker-safe
MODE=platform finish five worker safe package
WORKER_STARTED=slot_1_backend
WORKER_STARTED=slot_2_frontend
WORKER_STARTED=slot_3_ops
WORKER_STARTED=slot_4_data_cache
WORKER_STARTED=slot_5_tests_validation
COMPLETED_SLOTS=5
BLOCKED_SLOTS=0
TIMEOUT_SLOTS=0
PROGRAM_COMPLETION=75/100

```
## C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\.aays_real_runs\terrayield__071_platform_finish_5worker_safe__20260506_162453\slots\terrayield__071__slot_1_backend.md
```text
PROJECT=terrayield
DISPLAY_PROJECT=TerraYield
TASK_ID=terrayield-071-platform-finish-5worker-safe
SLOT=
slot_1_backend
AREA=
backend
STARTED=
2026-05-06T16:24:54
CHECK=backend_python_compile
Listing 'app'...
Listing 'app\\api'...
Listing 'app\\api\\routes'...
Listing 'app\\cli'...
Listing 'app\\clients'...
Listing 'app\\core'...
Listing 'app\\db'...
Listing 'app\\etl'...
Listing 'app\\etl\\match'...
Listing 'app\\etl\\normalize'...
Listing 'app\\etl\\publish'...
Listing 'app\\etl\\score'...
Listing 'app\\etl\\sources'...
Listing 'app\\etl\\sources\\facilities'...
Listing 'app\\etl\\sources\\market'...
Listing 'app\\middleware'...
Listing 'app\\schemas'...
Listing 'app\\services'...

CHECK=backend_route_scan

FullName                                                                                                               
--------                                                                                                               
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\aays_sales_history_layers.py          
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\aays_sales_layers.py                  
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\aays_sale_land_verification.py        
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\admin.py                              
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\brownfield.py                         
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\etl.py                                
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\facilities.py                         
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\health.py                             
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\listings.py                           
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\map_layers.py                         
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\parcels.py                            
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\proxy.py                              
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\sources.py                            
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\__init__.py                           
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\deps.py                                      
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\__init__.py                                  
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\cli\print_storage_status.py                      
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\cli\run_storage_state_sync_loop.py               
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\cli\wait_for_db.py                               
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\clients\supabase_rest.py                         
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\clients\__init__.py                              
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\core\config.py                                   
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\core\storage.py                                  
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\core\ttl_cache.py                                
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\core\__init__.py                                 
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\db\base.py                                       
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\db\geo.py                                        
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\db\models.py                                     
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\db\session.py                                    
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\db\__init__.py                                   
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\match\parcel_matcher.py                      
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\match\__init__.py                            
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\normalize\__init__.py                        
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\publish\parcel_signal_summary.py             
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\publish\__init__.py                          
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\score\__init__.py                            
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\facilities\base.py                   
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\facilities\__init__.py               
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\market\base.py                       
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\market\sample_csv.py                 
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\market\vendor_feed.py                
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\market\__init__.py                   
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\base.py                              
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\common.py                            
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\government_property_finder.py        
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\hmlr_inspire.py                      
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\hmlr_price_paid.py                   
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\homes_england_landhub.py             
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\http_client.py                       
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\local_authority_brownfield.py        
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\manual_listing_exports.py            
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\planning_data_brownfield.py          
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\sources\__init__.py                          
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\apply_repo_manual_match_overrides.py         
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\authority_checkpoint.py                      
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\backfill_listing_truth.py                    
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\boost_parcel_use_from_facilities.py          
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\bootstrap_homes_england_handoff.py           
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\build_authority_subset_manifest.py           
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\build_england_region_chunk_matrix.py         
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\build_local_brownfield_manifest_candidates.py
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\build_market_integration_package.py          
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\build_market_polygon_provenance.py           
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\check_sale_geometry_tier_counts.py           
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\cli.py                                       
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\disk_utils.py                                
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\england_all_sales_candidate_geometry_build...
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\england_deep_sales_source_confidence_boost...
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\england_region_partitions.py                 
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\england_sales_source_discovery_and_geometr...
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\enrich_public_listing_addresses.py           
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\enrich_public_listing_postcodes.py           
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\estimated_candidate_geometry_builder.py      
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\export_final_after_d_upgrade.py              
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\export_market_listing_parcel_package.py      
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\fill_market_listing_export_gaps.py           
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\find_deep_apply_db_matches.py                
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\full_autonomous_polygon_classifier.py        
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\import_final_sale_geometry_confidence_tabl...
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\etl\load_external_market_sales_evidence.py       



RESULT=slot_completed
FINISHED=2026-05-06T16:24:55

```
## C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\.aays_real_runs\terrayield__071_platform_finish_5worker_safe__20260506_162453\slots\terrayield__071__slot_2_frontend.md
```text
PROJECT=terrayield
DISPLAY_PROJECT=TerraYield
TASK_ID=terrayield-071-platform-finish-5worker-safe
SLOT=
slot_2_frontend
AREA=
frontend
STARTED=
2026-05-06T16:24:54
CHECK=frontend_config_scan

CHECK=map_layer_reference_scan

RESULT=slot_completed
FINISHED=2026-05-06T16:25:18

```
## C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\.aays_real_runs\terrayield__071_platform_finish_5worker_safe__20260506_162453\slots\terrayield__071__slot_3_ops.md
```text
PROJECT=terrayield
DISPLAY_PROJECT=TerraYield
TASK_ID=terrayield-071-platform-finish-5worker-safe
SLOT=
slot_3_ops
AREA=
ops
STARTED=
2026-05-06T16:24:55
CHECK=docker_ps
CONTAINER ID   IMAGE          COMMAND                  CREATED      STATUS        PORTS                    NAMES
60ddbee7b874   nginx:alpine   "/docker-entrypoint.ÔÇĞ"   5 days ago   Up 18 hours   127.0.0.1:8099->80/tcp   aays_london_topography_tiles

CHECK=runner_heartbeat
# AAYS ChatGPT Runner V4

Time: 
05.06.2026 16:24:52
Status: running 
terrayield-076-platform-check-5worker-retry-direct
BridgeRoot: 
C:\Users\cagda\Documents\chat_gpt_clone_1
ProjectRoot: 
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence
Mode: direct-run-and-push

RESULT=slot_completed
FINISHED=2026-05-06T16:24:55

```
## C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\.aays_real_runs\terrayield__071_platform_finish_5worker_safe__20260506_162453\slots\terrayield__071__slot_4_data_cache.md
```text
PROJECT=terrayield
DISPLAY_PROJECT=TerraYield
TASK_ID=terrayield-071-platform-finish-5worker-safe
SLOT=
slot_4_data_cache
AREA=
data_cache
STARTED=
2026-05-06T16:24:55
DATASET_EXISTS=True
ROWS=3110
COLUMNS=listing_id,provider_listing_id,title,listing_status,local_authority,postcode,address_text,parcel_name,ask_price,listing_url,latitude,longitude,point_wkt,geometry_wkt,geometry_geojson,sale_footprint_geojson,matched_parcel_ref,matched_inspire_id,planning_reference,title_numbers,site_area_m2,site_area_acres,location_notes,ingest_tag
RESULT=slot_completed
FINISHED=2026-05-06T16:24:55

```
## C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\.aays_real_runs\terrayield__071_platform_finish_5worker_safe__20260506_162453\slots\terrayield__071__slot_5_tests_validation.md
```text
PROJECT=terrayield
DISPLAY_PROJECT=TerraYield
TASK_ID=terrayield-071-platform-finish-5worker-safe
SLOT=
slot_5_tests_validation
AREA=
tests_validation
STARTED=
2026-05-06T16:24:55
CHECK=pytest_or_compile_fallback

=================================== ERRORS ====================================
______________ ERROR collecting tests/facility-adapter-5qtl4e17 _______________
..\..\..\..\AppData\Roaming\Python\Python312\site-packages\_pytest\runner.py:353: in from_call
    result: TResult | None = func()
                             ^^^^^^
..\..\..\..\AppData\Roaming\Python\Python312\site-packages\_pytest\runner.py:398: in collect
    return list(collector.collect())
           ^^^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Roaming\Python\Python312\site-packages\_pytest\main.py:557: in collect
    for direntry in scandir(self.path):
                    ^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Roaming\Python\Python312\site-packages\_pytest\pathlib.py:963: in scandir
    scandir_iter = os.scandir(path)
                   ^^^^^^^^^^^^^^^^
E   PermissionError: [WinError 5] Eri■im engellendi: 'C:\\Users\\cagda\\Documents\\GitHub\\AAYS\\terrayield_land_intelligence\\tests\\facility-adapter-5qtl4e17'
=========================== short test summary info ===========================
ERROR tests/facility-adapter-5qtl4e17 - PermissionError: [WinError 5] Eri■im ...
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 8.40s

RESULT=slot_completed
FINISHED=2026-05-06T16:25:05

```
