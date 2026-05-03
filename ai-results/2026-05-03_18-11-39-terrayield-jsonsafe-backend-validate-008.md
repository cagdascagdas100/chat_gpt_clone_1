# AAYS ChatGPT Runner V4 Result

## Task
JSON-safe TerraYield backend validation

## Task ID
terrayield-jsonsafe-backend-validate-008

## Progress
96%

## Action


## Time
05/03/2026 18:12:41

## Working Directory
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence

## Timeout Seconds
900

## Exit Code
0

## Output
``text
TASK: JSON-safe backend validation
PROGRESS: 96%
TIME:

3 Mayıs 2026 Pazar 18:11:40
--- files ---
EXISTS app/core/ttl_cache.py
EXISTS app/middleware/map_listings_cache.py
EXISTS app/main.py
EXISTS app/api/routes/aays_sales_layers.py
--- compile ---
app/core/ttl_cache.py: 
app/middleware/map_listings_cache.py: 
app/main.py: 
app/api/routes/aays_sales_layers.py: 
--- docker ps ---
--- endpoints two pass ---
PASS 1
FAIL /health error=Uzak sunucuya bağlanılamıyor
FAIL /openapi.json error=Uzak sunucuya bağlanılamıyor
FAIL /map/listings error=Uzak sunucuya bağlanılamıyor
FAIL /map/sales-history/status error=Uzak sunucuya bağlanılamıyor
FAIL /map/sales-history/external-evidence error=Uzak sunucuya bağlanılamıyor
FAIL /map/sales-history/parcels error=Uzak sunucuya bağlanılamıyor
FAIL /map/sales-history/combined error=Uzak sunucuya bağlanılamıyor
PASS 2
FAIL /health error=Uzak sunucuya bağlanılamıyor
FAIL /openapi.json error=Uzak sunucuya bağlanılamıyor
FAIL /map/listings error=Uzak sunucuya bağlanılamıyor
FAIL /map/sales-history/status error=Uzak sunucuya bağlanılamıyor
FAIL /map/sales-history/external-evidence error=Uzak sunucuya bağlanılamıyor
FAIL /map/sales-history/parcels error=Uzak sunucuya bağlanılamıyor
FAIL /map/sales-history/combined error=Uzak sunucuya bağlanılamıyor
--- recent api errors ---
JSONSAFE_BACKEND_VALIDATE_008_DONE



``

## Error
``text
docker : failed to connect to the docker API at npipe:////./pipe/dockerDesktopLinuxEngine; check if the path is correct
 and if the daemon is running: open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified.
At C:\Users\cagda\Documents\chat_gpt_clone_1\ai-tmp\task-terrayield-jsonsafe-backend-validate-008.ps1:1 char:695
+ ... er ps ---'; docker compose -f docker-compose.yml -f docker-compose.aa ...
+                 ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : NotSpecified: (failed to conne...file specified.:String) [], RemoteException
    + FullyQualifiedErrorId : NativeCommandError
 

``

