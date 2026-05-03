# AAYS ChatGPT Runner V4 Result

## Task
Runner V4 direct endpoint status check

## Task ID
terrayield-runner-v4-direct-status-002

## Progress
100%

## Action


## Time
05/03/2026 03:19:04

## Working Directory
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence

## Timeout Seconds
420

## Exit Code
0

## Output
``text
TASK: Runner V4 direct endpoint status check
PROGRESS: 100%
TIME:

3 Mayıs 2026 Pazar 03:18:46
--- compose ps with override ---
NAME                      IMAGE                    COMMAND                  SERVICE   CREATED      STATUS        PORTS
terrayield_land_postgis   postgis/postgis:16-3.4   "docker-entrypoint.sÔÇĞ"   db        2 days ago   Up 37 hours   0.0.0.0:55460->5432/tcp, [::]:55460->5432/tcp
--- api command ---
["bash","-lc","cd /app && alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8010"]
--- endpoint tests ---
OK /health status=200 ms=2698 bytes=137
OK /openapi.json status=200 ms=150 bytes=74388
OK /map/listings status=200 ms=9433 bytes=2910333
OK /map/sales-layers/verified-history status=200 ms=62 bytes=42
OK /map/sales-history/status status=200 ms=50 bytes=512
OK /map/sales-history/external-evidence status=200 ms=2662 bytes=1368759
OK /map/sales-history/parcels status=200 ms=415 bytes=132175
OK /map/sales-history/combined status=200 ms=2191 bytes=1398130
--- recent geography/status errors ---
DIRECT_STATUS_CHECK_DONE



``

## Error
``text

``

