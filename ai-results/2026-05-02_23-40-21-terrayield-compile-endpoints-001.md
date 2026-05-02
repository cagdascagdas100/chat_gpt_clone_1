# ChatGPT Runner Result

## Task
TerraYield compile and endpoint test

## Task ID
terrayield-compile-endpoints-001

## Progress
76%

## Time
05/02/2026 23:41:42

## Working Directory
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence

## Exit Code
0

## Command
Write-Output 'TASK: TerraYield compile ve endpoint testi'; Write-Output 'PROGRESS: 76%'; Write-Output 'ESTIMATED_WAIT: 3-5 dakika'; Write-Output 'START_TIME:'; Get-Date; Write-Output '--- PYTHON VERSION ---'; python --version 2>&1; Write-Output '--- PY_COMPILE KEY FILES ---'; python -m py_compile app\api\routes\aays_sales_layers.py app\main.py app\core\ttl_cache.py app\middleware\map_listings_cache.py 2>&1; Write-Output '--- DOCKER COMPOSE PS ---'; docker compose ps 2>&1; Write-Output '--- ENDPOINT TESTS ---'; $eps = @('/health','/openapi.json','/map/listings','/map/sales-layers/verified-history','/map/sales-history/status','/map/sales-history/external-evidence','/map/sales-history/parcels','/map/sales-history/combined'); foreach ($ep in $eps) { $url = 'http://localhost:8010' + $ep; Write-Output ('TEST ' + $ep); try { $r = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 25; Write-Output ('OK status=' + [string]$r.StatusCode + ' bytes=' + [string]$r.Content.Length) } catch { Write-Output ('FAIL ' + $_.Exception.Message) } }; Write-Output 'END_TIME:'; Get-Date; Write-Output 'COMPILE_ENDPOINTS_DONE'

## Output
TASK: TerraYield compile ve endpoint testi
PROGRESS: 76%
ESTIMATED_WAIT: 3-5 dakika
START_TIME:

2 Mayıs 2026 Cumartesi 23:40:22
--- PYTHON VERSION ---
Python 3.12.6
--- PY_COMPILE KEY FILES ---
--- DOCKER COMPOSE PS ---
NAME                      IMAGE                    COMMAND                  SERVICE   CREATED       STATUS        PORTS
terrayield_land_api       python:3.12-slim         "bash -lc 'pip instaÔÇĞ"   api       9 hours ago   Up 9 hours    0.0.0.0:8010->8010/tcp, [::]:8010->8010/tcp
terrayield_land_postgis   postgis/postgis:16-3.4   "docker-entrypoint.sÔÇĞ"   db        2 days ago    Up 34 hours   0.0.0.0:55460->5432/tcp, [::]:55460->5432/tcp
--- ENDPOINT TESTS ---
TEST /health
OK status=200 bytes=137
TEST /openapi.json
OK status=200 bytes=74388
TEST /map/listings
OK status=200 bytes=2910333
TEST /map/sales-layers/verified-history
OK status=200 bytes=42
TEST /map/sales-history/status
FAIL The operation has timed out.
TEST /map/sales-history/external-evidence
OK status=200 bytes=1368759
TEST /map/sales-history/parcels
OK status=200 bytes=132175
TEST /map/sales-history/combined
OK status=200 bytes=1398130
END_TIME:
2 Mayıs 2026 Cumartesi 23:41:29
COMPILE_ENDPOINTS_DONE



