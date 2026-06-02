# AAYS ChatGPT Runner V4 Result

## Task
TerraYield API dependency bootstrap and endpoint validation

## Task ID
terrayield-recovery-017-api-deps

## Progress
98%

## Action


## Time
05/04/2026 00:30:12

## Working Directory
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence

## Timeout Seconds
1800

## Exit Code
0

## Output
``text
[0 s] TASK: TerraYield recovery 017 API dependency bootstrap
[0 s] PROGRESS: 98%
[0 s] PROJECT=C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence
[0 s] REPORT_DIR=C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\.aays_next_fix\recovery_017_api_deps_20260504_000204
[0 s] --- compose config before ---
name: terrayield_land_intelligence
services:
  api:
    command:
      - sh
      - -lc
      - cd /app && alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8010
    container_name: terrayield_land_api
    depends_on:
      db:
        condition: service_started
        required: true
    environment:
      TYLI_ALLOW_SAMPLE_DATA: "true"
      TYLI_APP_ENV: development
      TYLI_APP_HOST: 0.0.0.0
      TYLI_APP_NAME: TerraYield Land Intelligence
      TYLI_APP_PORT: "8010"
      TYLI_CORS_ORIGINS: http://127.0.0.1:8080,http://localhost:8080,http://127.0.0.1:8535,http://localhost:8535,http://127.0.0.1:8010,http://localhost:8010,http://127.0.0.1:8011,http://localhost:8011,http://127.0.0.1:8012,http://localhost:8012
      TYLI_DATABASE_URL: postgresql+psycopg://postgres:postgres@db:5432/terrayield_land
      TYLI_DB_PORT: "55460"
      TYLI_DELETE_RAW_AFTER_SUCCESS: "true"
      TYLI_EXTERNAL_RAW_STORAGE_DIR: E:\AAYS_DATA\terrayield_land_intelligence\raw
      TYLI_EXTERNAL_RUNTIME_TEMP_DIR: E:\AAYS_DATA\terrayield_land_intelligence\tmp
      TYLI_FUZZY_SIMILARITY_THRESHOLD: "0.65"
      TYLI_HOMES_ENGLAND_PAGE_SIZE: "200"
      TYLI_HOMES_ENGLAND_URL: https://services-eu1.arcgis.com/yo0w4PgP4XL49bfF/ArcGIS/rest/services/Homes_England_Land_Hub_Sites/FeatureServer/0/query
      TYLI_HTTP_MAX_RETRIES: "3"
      TYLI_HTTP_RETRY_BACKOFF_S: "1.5"
      TYLI_HTTP_TIMEOUT_S: "90"
      TYLI_HTTP_USER_AGENT: TerraYield-Land-Intelligence/0.1
      TYLI_INSPIRE_ASSUME_CRS: "27700"
      TYLI_INSPIRE_AUTHORITY_LIMIT: "0"
      TYLI_INSPIRE_AUTHORITY_OFFSET: "0"
      TYLI_INSPIRE_DELETE_ZIP_AFTER_PARSE: "true"
      TYLI_INSPIRE_FORCE_REDOWNLOAD: "false"
      TYLI_INSPIRE_MANIFEST_PATH: C:\Users\cagda\Documents\GitHub\AAYS\data\inspire\manifest_england.json
      TYLI_INSPIRE_STALE_AFTER_DAYS: "45"
      TYLI_LANDHUB_STALE_AFTER_DAYS: "45"
      TYLI_LOCAL_BROWNFIELD_CANDIDATE_MANIFEST_CSV_PATH: C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\sample_data\local_authority_brownfield_manifest_candidates.csv
      TYLI_LOCAL_BROWNFIELD_CANDIDATE_MANIFEST_PATH: C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\sample_data\local_authority_brownfield_manifest_candidates.json
      TYLI_LOCAL_BROWNFIELD_MANIFEST_PATH: C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\sample_data\local_authority_brownfield_manifest.json
      TYLI_LOCAL_BROWNFIELD_STALE_AFTER_DAYS: "365"
      TYLI_MARKET_STALE_AFTER_DAYS: "14"
      TYLI_MAX_RAW_FILES_PER_SOURCE: "0"
      TYLI_MIN_FREE_DISK_GB: "2"
      TYLI_PLANNING_BROWNFIELD_FALLBACK_URLS: https://files.planning.data.gov.uk/dataset/brownfield-land.geojson,https://files.planning.data.gov.uk/dataset/brownfield-land.json
      TYLI_PLANNING_BROWNFIELD_PAGE_LIMIT: "0"
      TYLI_PLANNING_BROWNFIELD_PAGE_SIZE: "500"
      TYLI_PLANNING_BROWNFIELD_URL: https://www.planning.data.gov.uk/entity.geojson?dataset=brownfield-land
      TYLI_PLANNING_DATA_STALE_AFTER_DAYS: "90"
      TYLI_POINT_MATCH_RADIUS_M: "100"
      TYLI_PRICE_PAID_FALLBACK_URLS: https://price-paid-data.publicdata.landregistry.gov.uk/pp-monthly-update-new-version.csv,https://prod.publicdata.landregistry.gov.uk.s3-website-eu-west-1.amazonaws.com/pp-monthly-update-new-version.csv
      TYLI_PRICE_PAID_STALE_AFTER_DAYS: "90"
      TYLI_PRICE_PAID_URL: https://price-paid-data.publicdata.landregistry.gov.uk/pp-monthly-update-new-version.csv
      TYLI_RAW_STORAGE_DIR: ./data/raw
      TYLI_RUNTIME_TEMP_DIR: ./data/tmp
      TYLI_SUPABASE_ENABLED: "true"
      TYLI_SUPABASE_SCHEMA: public
      TYLI_SUPABASE_SERVICE_ROLE_KEY: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imdncm5mamN6cGR6cW14am52a2xmIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MzQ5NTY5NCwiZXhwIjoyMDg5MDcxNjk0fQ.-eYHkjFE_MUXyaNMMNB5fwm8G_TuhXNdKhF8BRw7r44
      TYLI_SUPABASE_TABLE: land_listings
      TYLI_SUPABASE_URL: https://ggrnfjczpdzqmxjnvklf.supabase.co
      TYLI_SYNC_EXTERNAL_STATE_ON_STARTUP: "true"
    image: python:3.12-slim
    networks:
      default: null
    ports:
      - mode: ingress
        target: 8010
        published: "8010"
        protocol: tcp
    volumes:
      - type: bind
        source: C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence
        target: /app
        bind: {}
      - type: bind
        source: C:\Users\cagda\Documents\GitHub\AAYS\england_map_web
        target: /app/england_map_web
        read_only: true
        bind: {}
    working_dir: /app
  db:
    container_name: terrayield_land_postgis
    environment:
      POSTGRES_DB: terrayield_land
      POSTGRES_PASSWORD: postgres
      POSTGRES_USER: postgres
    image: postgis/postgis:16-3.4
    networks:
      default: null
    ports:
      - mode: ingress
        target: 5432
        published: "55460"
        protocol: tcp
    volumes:
      - type: volume
        source: terrayield_land_pgdata
        target: /var/lib/postgresql/data
        volume: {}
networks:
  default:
    name: terrayield_land_intelligence_default
volumes:
  terrayield_land_pgdata:
    name: terrayield_land_intelligence_terrayield_land_pgdata

[1 s] compose config before EXIT=0
[1 s] --- patch compose API command to install deps and run python modules ---
[1 s] BACKUP docker-compose.aays-fast-start.yml
[1 s] PATCHED docker-compose.aays-fast-start.yml api dependency bootstrap
[1 s] --- CONTENT docker-compose.aays-fast-start.yml ---
[1 s] BACKUP docker-compose.yml
[1 s] PATCHED docker-compose.yml api dependency bootstrap
[1 s] --- CONTENT docker-compose.yml ---
[1 s] --- compile focused host check ---
[1 s] COMPILE app\core\ttl_cache.py EXIT=0
[1 s] COMPILE app\middleware\map_listings_cache.py EXIT=0
[2 s] COMPILE app\main.py EXIT=0
[2 s] COMPILE app\api\routes\aays_sales_layers.py EXIT=0
[2 s] COMPILE app\api\routes\aays_sales_history_layers.py EXIT=0
[2 s] --- compose config after ---
name: terrayield_land_intelligence
services:
  api:
    command: []
    container_name: terrayield_land_api
    depends_on:
      db:
        condition: service_started
        required: true
    environment:
      TYLI_ALLOW_SAMPLE_DATA: "true"
      TYLI_APP_ENV: development
      TYLI_APP_HOST: 0.0.0.0
      TYLI_APP_NAME: TerraYield Land Intelligence
      TYLI_APP_PORT: "8010"
      TYLI_CORS_ORIGINS: http://127.0.0.1:8080,http://localhost:8080,http://127.0.0.1:8535,http://localhost:8535,http://127.0.0.1:8010,http://localhost:8010,http://127.0.0.1:8011,http://localhost:8011,http://127.0.0.1:8012,http://localhost:8012
      TYLI_DATABASE_URL: postgresql+psycopg://postgres:postgres@db:5432/terrayield_land
      TYLI_DB_PORT: "55460"
      TYLI_DELETE_RAW_AFTER_SUCCESS: "true"
      TYLI_EXTERNAL_RAW_STORAGE_DIR: E:\AAYS_DATA\terrayield_land_intelligence\raw
      TYLI_EXTERNAL_RUNTIME_TEMP_DIR: E:\AAYS_DATA\terrayield_land_intelligence\tmp
      TYLI_FUZZY_SIMILARITY_THRESHOLD: "0.65"
      TYLI_HOMES_ENGLAND_PAGE_SIZE: "200"
      TYLI_HOMES_ENGLAND_URL: https://services-eu1.arcgis.com/yo0w4PgP4XL49bfF/ArcGIS/rest/services/Homes_England_Land_Hub_Sites/FeatureServer/0/query
      TYLI_HTTP_MAX_RETRIES: "3"
      TYLI_HTTP_RETRY_BACKOFF_S: "1.5"
      TYLI_HTTP_TIMEOUT_S: "90"
      TYLI_HTTP_USER_AGENT: TerraYield-Land-Intelligence/0.1
      TYLI_INSPIRE_ASSUME_CRS: "27700"
      TYLI_INSPIRE_AUTHORITY_LIMIT: "0"
      TYLI_INSPIRE_AUTHORITY_OFFSET: "0"
      TYLI_INSPIRE_DELETE_ZIP_AFTER_PARSE: "true"
      TYLI_INSPIRE_FORCE_REDOWNLOAD: "false"
      TYLI_INSPIRE_MANIFEST_PATH: C:\Users\cagda\Documents\GitHub\AAYS\data\inspire\manifest_england.json
      TYLI_INSPIRE_STALE_AFTER_DAYS: "45"
      TYLI_LANDHUB_STALE_AFTER_DAYS: "45"
      TYLI_LOCAL_BROWNFIELD_CANDIDATE_MANIFEST_CSV_PATH: C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\sample_data\local_authority_brownfield_manifest_candidates.csv
      TYLI_LOCAL_BROWNFIELD_CANDIDATE_MANIFEST_PATH: C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\sample_data\local_authority_brownfield_manifest_candidates.json
      TYLI_LOCAL_BROWNFIELD_MANIFEST_PATH: C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\sample_data\local_authority_brownfield_manifest.json
      TYLI_LOCAL_BROWNFIELD_STALE_AFTER_DAYS: "365"
      TYLI_MARKET_STALE_AFTER_DAYS: "14"
      TYLI_MAX_RAW_FILES_PER_SOURCE: "0"
      TYLI_MIN_FREE_DISK_GB: "2"
      TYLI_PLANNING_BROWNFIELD_FALLBACK_URLS: https://files.planning.data.gov.uk/dataset/brownfield-land.geojson,https://files.planning.data.gov.uk/dataset/brownfield-land.json
      TYLI_PLANNING_BROWNFIELD_PAGE_LIMIT: "0"
      TYLI_PLANNING_BROWNFIELD_PAGE_SIZE: "500"
      TYLI_PLANNING_BROWNFIELD_URL: https://www.planning.data.gov.uk/entity.geojson?dataset=brownfield-land
      TYLI_PLANNING_DATA_STALE_AFTER_DAYS: "90"
      TYLI_POINT_MATCH_RADIUS_M: "100"
      TYLI_PRICE_PAID_FALLBACK_URLS: https://price-paid-data.publicdata.landregistry.gov.uk/pp-monthly-update-new-version.csv,https://prod.publicdata.landregistry.gov.uk.s3-website-eu-west-1.amazonaws.com/pp-monthly-update-new-version.csv
      TYLI_PRICE_PAID_STALE_AFTER_DAYS: "90"
      TYLI_PRICE_PAID_URL: https://price-paid-data.publicdata.landregistry.gov.uk/pp-monthly-update-new-version.csv
      TYLI_RAW_STORAGE_DIR: ./data/raw
      TYLI_RUNTIME_TEMP_DIR: ./data/tmp
      TYLI_SUPABASE_ENABLED: "true"
      TYLI_SUPABASE_SCHEMA: public
      TYLI_SUPABASE_SERVICE_ROLE_KEY: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imdncm5mamN6cGR6cW14am52a2xmIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MzQ5NTY5NCwiZXhwIjoyMDg5MDcxNjk0fQ.-eYHkjFE_MUXyaNMMNB5fwm8G_TuhXNdKhF8BRw7r44
      TYLI_SUPABASE_TABLE: land_listings
      TYLI_SUPABASE_URL: https://ggrnfjczpdzqmxjnvklf.supabase.co
      TYLI_SYNC_EXTERNAL_STATE_ON_STARTUP: "true"
    image: python:3.12-slim
    networks:
      default: null
    ports:
      - mode: ingress
        target: 8010
        published: "8010"
        protocol: tcp
    volumes:
      - type: bind
        source: C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence
        target: /app
        bind: {}
      - type: bind
        source: C:\Users\cagda\Documents\GitHub\AAYS\england_map_web
        target: /app/england_map_web
        read_only: true
        bind: {}
    working_dir: /app
  db:
    container_name: terrayield_land_postgis
    environment:
      POSTGRES_DB: terrayield_land
      POSTGRES_PASSWORD: postgres
      POSTGRES_USER: postgres
    image: postgis/postgis:16-3.4
    networks:
      default: null
    ports:
      - mode: ingress
        target: 5432
        published: "55460"
        protocol: tcp
    volumes:
      - type: volume
        source: terrayield_land_pgdata
        target: /var/lib/postgresql/data
        volume: {}
networks:
  default:
    name: terrayield_land_intelligence_default
volumes:
  terrayield_land_pgdata:
    name: terrayield_land_intelligence_terrayield_land_pgdata

[2 s] compose config after EXIT=0
[2 s] --- remove api ---
docker :  Container terrayield_land_api Stopping 
At C:\Users\cagda\Documents\chat_gpt_clone_1\ai-task-scripts\terrayield_recovery_017_api_deps.ps1:57 char:23
+ ... move api" { docker compose -f docker-compose.yml -f docker-compose.aa ...
+                 ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : NotSpecified: ( Container terrayield_land_api Stopping :String) [], RemoteException
    + FullyQualifiedErrorId : NativeCommandError
 
 Container terrayield_land_api Stopped 
Going to remove terrayield_land_api
 Container terrayield_land_api Removing 
 Container terrayield_land_api Removed 

[3 s] remove api EXIT=0
[3 s] --- up stack after dependency bootstrap ---
docker :  Container terrayield_land_postgis Running 
At C:\Users\cagda\Documents\chat_gpt_clone_1\ai-task-scripts\terrayield_recovery_017_api_deps.ps1:58 char:48
+ ... ootstrap" { docker compose -f docker-compose.yml -f docker-compose.aa ...
+                 ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : NotSpecified: ( Container terr...ostgis Running :String) [], RemoteException
    + FullyQualifiedErrorId : NativeCommandError
 
 Container terrayield_land_api Creating 
 Container terrayield_land_api Created 
 Container terrayield_land_api Starting 
 Container terrayield_land_api Started 

[4 s] up stack after dependency bootstrap EXIT=0
[4 s] --- compose ps after up ---
NAME                      IMAGE                    COMMAND                  SERVICE   CREATED         STATUS             PORTS
terrayield_land_api       python:3.12-slim         "python3"                api       3 seconds ago   Up 1 second        0.0.0.0:8010->8010/tcp, [::]:8010->8010/tcp
terrayield_land_postgis   postgis/postgis:16-3.4   "docker-entrypoint.sÔÇĞ"   db        3 days ago      Up About an hour   0.0.0.0:55460->5432/tcp, [::]:55460->5432/tcp

[5 s] compose ps after up EXIT=0
[60 s] WAIT_API 6/180
[116 s] WAIT_API 12/180
[171 s] WAIT_API 18/180
[226 s] WAIT_API 24/180
[281 s] WAIT_API 30/180
[336 s] WAIT_API 36/180
[391 s] WAIT_API 42/180
[446 s] WAIT_API 48/180
[501 s] WAIT_API 54/180
[556 s] WAIT_API 60/180
[612 s] WAIT_API 66/180
[667 s] WAIT_API 72/180
[722 s] WAIT_API 78/180
[776 s] WAIT_API 84/180
[831 s] WAIT_API 90/180
[886 s] WAIT_API 96/180
[941 s] WAIT_API 102/180
[996 s] WAIT_API 108/180
[1051 s] WAIT_API 114/180
[1105 s] WAIT_API 120/180
[1160 s] WAIT_API 126/180
[1215 s] WAIT_API 132/180
[1270 s] WAIT_API 138/180
[1325 s] WAIT_API 144/180
[1380 s] WAIT_API 150/180
[1434 s] WAIT_API 156/180
[1489 s] WAIT_API 162/180
[1544 s] WAIT_API 168/180
[1599 s] WAIT_API 174/180
[1654 s] WAIT_API 180/180
[1687 s] --- compose ps final ---
NAME                      IMAGE                    COMMAND                  SERVICE   CREATED          STATUS                      PORTS
terrayield_land_api       python:3.12-slim         "python3"                api       28 minutes ago   Exited (0) 28 minutes ago   
terrayield_land_postgis   postgis/postgis:16-3.4   "docker-entrypoint.sÔÇĞ"   db        3 days ago       Up 2 hours                  0.0.0.0:55460->5432/tcp, [::]:55460->5432/tcp

[1687 s] compose ps final EXIT=0
[1687 s] --- api logs tail ---
SUMMARY_FILE=C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\.aays_next_fix\recovery_017_api_deps_20260504_000204\summary.md
DETAIL_FILE=C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\.aays_next_fix\recovery_017_api_deps_20260504_000204\detail.txt
BACKUP_DIR=C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\.aays_next_fix\recovery_017_api_deps_20260504_000204\backup
RESULT=api_not_ready
COMPILE_OK=True
API_READY=False
ELAPSED_SECONDS=1687
RECOVERY_017_API_DEPS_DONE

``

## Error
``text

``

