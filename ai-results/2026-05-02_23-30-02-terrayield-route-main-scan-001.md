# ChatGPT Runner Result

## Task
TerraYield route and main detail scan

## Task ID
terrayield-route-main-scan-001

## Progress
68%

## Time
05/02/2026 23:30:03

## Working Directory
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence

## Exit Code
0

## Command
Write-Output 'TASK: TerraYield route/main detay taramasi'; Write-Output 'PROGRESS: 68%'; Write-Output 'ESTIMATED_WAIT: 2-3 dakika'; Write-Output 'START_TIME:'; Get-Date; Write-Output 'ROUTE_FILE_EXISTS:'; Test-Path 'app\api\routes\aays_sales_layers.py'; Write-Output 'MAIN_FILE_EXISTS:'; Test-Path 'app\main.py'; Write-Output '--- ROUTE GEOGRAPHY LINES ---'; if (Test-Path 'app\api\routes\aays_sales_layers.py') { Select-String -Path 'app\api\routes\aays_sales_layers.py' -Pattern 'ST_Area|::geography|area_m2|ST_SRID|ST_Transform|ST_SetSRID' -CaseSensitive:$false | Select-Object -First 120 | ForEach-Object { $_.LineNumber.ToString() + ': ' + $_.Line } }; Write-Output '--- MAIN MIDDLEWARE LINES ---'; if (Test-Path 'app\main.py') { Select-String -Path 'app\main.py' -Pattern 'MapListingsCacheMiddleware|add_middleware|middleware|FastAPI|CORSMiddleware' -CaseSensitive:$false | Select-Object -First 120 | ForEach-Object { $_.LineNumber.ToString() + ': ' + $_.Line } }; Write-Output '--- CACHE FILES ---'; Write-Output ('ttl_cache=' + (Test-Path 'app\core\ttl_cache.py')); Write-Output ('map_listings_cache=' + (Test-Path 'app\middleware\map_listings_cache.py')); Write-Output 'END_TIME:'; Get-Date; Write-Output 'ROUTE_MAIN_SCAN_DONE'

## Output
TASK: TerraYield route/main detay taramasi
PROGRESS: 68%
ESTIMATED_WAIT: 2-3 dakika
START_TIME:

2 Mayıs 2026 Cumartesi 23:30:03
ROUTE_FILE_EXISTS:
True
MAIN_FILE_EXISTS:
True
--- ROUTE GEOGRAPHY LINES ---
52:   when ST_SRID(p.geometry) = 4326 then ST_Area(p.geometry::geography)
53:   when ST_SRID(p.geometry) > 0 then ST_Area(ST_Transform(p.geometry, 4326)::geography)
54:   else ST_Area(ST_SetSRID(p.geometry, 4326)::geography)
55: end as area_m2,
66:           when ST_SRID(p.geometry) = 0 then ST_AsGeoJSON(p.geometry)::jsonb
67:           else ST_AsGeoJSON(ST_Transform(p.geometry, 4326))::jsonb
91:             'area_m2', area_m2,
139:   when ST_SRID(p.geometry) = 4326 then ST_Area(p.geometry::geography)
140:   when ST_SRID(p.geometry) > 0 then ST_Area(ST_Transform(p.geometry, 4326)::geography)
141:   else ST_Area(ST_SetSRID(p.geometry, 4326)::geography)
142: end as area_m2,
147:         h.latest_sale_area_m2,
154:           when ST_SRID(p.geometry) = 0 then ST_AsGeoJSON(p.geometry)::jsonb
155:           else ST_AsGeoJSON(ST_Transform(p.geometry, 4326))::jsonb
178:             'area_m2', area_m2,
184:             'latest_sale_area_m2', latest_sale_area_m2,
--- MAIN MIDDLEWARE LINES ---
7: from fastapi import FastAPI
8: from fastapi.middleware.cors import CORSMiddleware
17: app = FastAPI(
23: app.add_middleware(
24:     CORSMiddleware,
74: from app.middleware.map_listings_cache import MapListingsCacheMiddleware
79:     app.add_middleware(MapListingsCacheMiddleware)
81:     print(f"[AAYS] MapListingsCacheMiddleware not enabled: {_aays_map_listings_cache_error}")
--- CACHE FILES ---
ttl_cache=True
map_listings_cache=True
END_TIME:
2 Mayıs 2026 Cumartesi 23:30:03
ROUTE_MAIN_SCAN_DONE



