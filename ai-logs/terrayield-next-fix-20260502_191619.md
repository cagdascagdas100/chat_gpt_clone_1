# TerraYield Next Fix Stabilization Report

Run ID: 20260502_191619  
Project: C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence  
Report Directory: C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\.aays_next_fix\run_20260502_191619  
Progress: 100%

## Patch Results

- ST_Area geography patch: PATCHED_EXACT_ST_AREA_GEOGRAPHY
- main.py middleware patch: IMPORT_ALREADY_PRESENT;ADD_MIDDLEWARE_APPENDED
- ttl_cache.py: ensured
- map_listings_cache.py: ensured

## Endpoint Results

Passed: 7 / 8


endpoint                             url                                                          ok status   bytes err
                                                                                                                    or 
--------                             ---                                                          -- ------   ----- ---
/health                              http://localhost:8010/health                               True    200     139    
/openapi.json                        http://localhost:8010/openapi.json                         True    200   74390    
/map/listings                        http://localhost:8010/map/listings                         True    200 2910335    
/map/sales-layers/verified-history   http://localhost:8010/map/sales-layers/verified-history    True    200      44    
/map/sales-history/status            http://localhost:8010/map/sales-history/status            False              0 The
/map/sales-history/external-evidence http://localhost:8010/map/sales-history/external-evidence  True    200 1368761    
/map/sales-history/parcels           http://localhost:8010/map/sales-history/parcels            True    200  132177    
/map/sales-history/combined          http://localhost:8010/map/sales-history/combined           True    200 1398132    




## Failed Endpoints


endpoint                  url                                               ok status bytes error                      
--------                  ---                                               -- ------ ----- -----                      
/map/sales-history/status http://localhost:8010/map/sales-history/status False            0 The operation has timed ...




## Important Notes

- London 181 / sale_ready 172 veri seti bu işlemde tekrar taranmadı.
- Bu çalışma API stabilizasyonu ve PostGIS geography hatasına odaklandı.
- Veri invariant doğrulaması doğru dump/import/volume bulunmadan yapılmış sayılmaz.
- Backup klasörü: C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\.aays_next_fix\run_20260502_191619\backup

## Key Files

- Route file: C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\api\routes\aays_sales_layers.py
- Main file: C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\main.py
- TTL cache: C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\core\ttl_cache.py
- Middleware: C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\middleware\map_listings_cache.py
- Full log: C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\.aays_next_fix\run_20260502_191619\FULL_LOG.txt
- Endpoint JSON: C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\.aays_next_fix\run_20260502_191619\endpoint_results.json
