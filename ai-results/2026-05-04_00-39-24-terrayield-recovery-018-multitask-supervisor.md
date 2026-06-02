# AAYS ChatGPT Runner V4 Result

## Task
TerraYield parallel diagnosis, compose command recovery, and API validation

## Task ID
terrayield-recovery-018-multitask-supervisor

## Progress
98%

## Action


## Time
05/04/2026 00:44:23

## Working Directory
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence

## Timeout Seconds
1800

## Exit Code
0

## Output
``text
[0 s] TASK: TerraYield recovery 018 multitask supervisor
[0 s] MODE: parallel diagnosis + compose command override + API-only recovery
[0 s] REASON: recovery 017 produced compile_ok=True but api_not_ready; compose config showed API command became empty and container exited 0
[0 s] PROJECT=C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence
[0 s] REPORT_DIR=C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\.aays_next_fix\recovery_018_multitask_supervisor_20260504_003925
[0 s] WROTE docker-compose.aays-api-command.yml to override broken/empty API command
[115 s] API_HEALTH_INITIAL=False
[115 s] API is not healthy; starting API-only recovery path.
[115 s] --- compose config with API command override ---
name: terrayield_land_intelligence
services:
  api:
    command:
      - sh
      - -lc
      - cd /app && python -m pip install --no-cache-dir -e . && python -m alembic upgrade head && python -m uvicorn app.main:app --host 0.0.0.0 --port 8010
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

[115 s] compose config with API command override EXIT=0
name: terrayield_land_intelligence
services:
  api:
    command:
      - sh
      - -lc
      - cd /app && python -m pip install --no-cache-dir -e . && python -m alembic upgrade head && python -m uvicorn app.main:app --host 0.0.0.0 --port 8010
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

[115 s] --- start db only ---
docker :  Container terrayield_land_postgis Running 
At C:\Users\cagda\Documents\chat_gpt_clone_1\ai-task-scripts\terrayield_recovery_018_multitask_supervisor.ps1:153 char:
33
+ ...  Run-Capture 'start db only' { docker compose @ComposeArgs up -d db }
+                                    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : NotSpecified: ( Container terr...ostgis Running :String) [], RemoteException
    + FullyQualifiedErrorId : NativeCommandError
 

[116 s] start db only EXIT=0
docker :  Container terrayield_land_postgis Running 
At C:\Users\cagda\Documents\chat_gpt_clone_1\ai-task-scripts\terrayield_recovery_018_multitask_supervisor.ps1:153 char:
33
+ ...  Run-Capture 'start db only' { docker compose @ComposeArgs up -d db }
+                                    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : NotSpecified: ( Container terr...ostgis Running :String) [], RemoteException
    + FullyQualifiedErrorId : NativeCommandError
 

[116 s] --- remove stale api container only ---
docker :  Container terrayield_land_api Stopping 
At C:\Users\cagda\Documents\chat_gpt_clone_1\ai-task-scripts\terrayield_recovery_018_multitask_supervisor.ps1:154 char:
51
+ ...  stale api container only' { docker compose @ComposeArgs rm -sf api }
+                                  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : NotSpecified: ( Container terrayield_land_api Stopping :String) [], RemoteException
    + FullyQualifiedErrorId : NativeCommandError
 
 Container terrayield_land_api Stopped 
Going to remove terrayield_land_api
 Container terrayield_land_api Removing 
 Container terrayield_land_api Removed 

[117 s] remove stale api container only EXIT=0
docker :  Container terrayield_land_api Stopping 
At C:\Users\cagda\Documents\chat_gpt_clone_1\ai-task-scripts\terrayield_recovery_018_multitask_supervisor.ps1:154 char:
51
+ ...  stale api container only' { docker compose @ComposeArgs rm -sf api }
+                                  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : NotSpecified: ( Container terrayield_land_api Stopping :String) [], RemoteException
    + FullyQualifiedErrorId : NativeCommandError
 
 Container terrayield_land_api Stopped 
Going to remove terrayield_land_api
 Container terrayield_land_api Removing 
 Container terrayield_land_api Removed 

[117 s] --- api dependency bootstrap and migration in one-shot container ---
docker :  Container terrayield_land_postgis Running 
At C:\Users\cagda\Documents\chat_gpt_clone_1\ai-task-scripts\terrayield_recovery_018_multitask_supervisor.ps1:155 char:
80
+ ... ontainer' { docker compose @ComposeArgs run --rm api sh -lc 'cd /app  ...
+                 ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : NotSpecified: ( Container terr...ostgis Running :String) [], RemoteException
    + FullyQualifiedErrorId : NativeCommandError
 
 Container terrayield_land_intelligence-api-run-30d3fa7d2509 Creating 
 Container terrayield_land_intelligence-api-run-30d3fa7d2509 Created 
Obtaining file:///app
  Installing build dependencies: started
  Installing build dependencies: finished with status 'done'
  Checking if build backend supports build_editable: started
  Checking if build backend supports build_editable: finished with status 'done'
  Getting requirements to build editable: started
  Getting requirements to build editable: finished with status 'done'
  Preparing editable metadata (pyproject.toml): started
  Preparing editable metadata (pyproject.toml): finished with status 'done'
Collecting alembic>=1.14.1 (from terrayield-land-intelligence==0.1.0)
  Downloading alembic-1.18.4-py3-none-any.whl.metadata (7.2 kB)
Collecting fastapi>=0.116.0 (from terrayield-land-intelligence==0.1.0)
  Downloading fastapi-0.136.1-py3-none-any.whl.metadata (28 kB)
Collecting geoalchemy2>=0.16.0 (from terrayield-land-intelligence==0.1.0)
  Downloading geoalchemy2-0.19.0-py3-none-any.whl.metadata (2.1 kB)
Collecting geopandas>=1.0.1 (from terrayield-land-intelligence==0.1.0)
  Downloading geopandas-1.1.3-py3-none-any.whl.metadata (2.3 kB)
Collecting httpx>=0.28.0 (from terrayield-land-intelligence==0.1.0)
  Downloading httpx-0.28.1-py3-none-any.whl.metadata (7.1 kB)
Collecting pandas>=2.2.3 (from terrayield-land-intelligence==0.1.0)
  Downloading pandas-3.0.2-cp312-cp312-manylinux_2_24_x86_64.manylinux_2_28_x86_64.whl.metadata (79 kB)
Collecting psycopg>=3.2.0 (from psycopg[binary]>=3.2.0->terrayield-land-intelligence==0.1.0)
  Downloading psycopg-3.3.4-py3-none-any.whl.metadata (4.3 kB)
Collecting pyproj>=3.7.1 (from terrayield-land-intelligence==0.1.0)
  Downloading pyproj-3.7.2-cp312-cp312-manylinux_2_28_x86_64.whl.metadata (31 kB)
Collecting pyogrio>=0.11.1 (from terrayield-land-intelligence==0.1.0)
  Downloading pyogrio-0.12.1-cp312-cp312-manylinux_2_28_x86_64.whl.metadata (5.9 kB)
Collecting pydantic-settings>=2.8.0 (from terrayield-land-intelligence==0.1.0)
  Downloading pydantic_settings-2.14.0-py3-none-any.whl.metadata (3.4 kB)
Collecting python-dateutil>=2.9.0 (from terrayield-land-intelligence==0.1.0)
  Downloading python_dateutil-2.9.0.post0-py2.py3-none-any.whl.metadata (8.4 kB)
Collecting python-dotenv>=1.0.1 (from terrayield-land-intelligence==0.1.0)
  Downloading python_dotenv-1.2.2-py3-none-any.whl.metadata (27 kB)
Collecting requests>=2.32.0 (from terrayield-land-intelligence==0.1.0)
  Downloading requests-2.33.1-py3-none-any.whl.metadata (4.8 kB)
Collecting shapely>=2.0.7 (from terrayield-land-intelligence==0.1.0)
  Downloading shapely-2.1.2-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.whl.metadata (6.8 kB)
Collecting sqlalchemy>=2.0.38 (from terrayield-land-intelligence==0.1.0)
  Downloading sqlalchemy-2.0.49-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.metadata (9.5 kB)
Collecting uvicorn>=0.34.0 (from uvicorn[standard]>=0.34.0->terrayield-land-intelligence==0.1.0)
  Downloading uvicorn-0.46.0-py3-none-any.whl.metadata (6.7 kB)
Collecting Mako (from alembic>=1.14.1->terrayield-land-intelligence==0.1.0)
  Downloading mako-1.3.12-py3-none-any.whl.metadata (2.9 kB)
Collecting typing-extensions>=4.12 (from alembic>=1.14.1->terrayield-land-intelligence==0.1.0)
  Downloading typing_extensions-4.15.0-py3-none-any.whl.metadata (3.3 kB)
Collecting starlette>=0.46.0 (from fastapi>=0.116.0->terrayield-land-intelligence==0.1.0)
  Downloading starlette-1.0.0-py3-none-any.whl.metadata (6.3 kB)
Collecting pydantic>=2.9.0 (from fastapi>=0.116.0->terrayield-land-intelligence==0.1.0)
  Downloading pydantic-2.13.3-py3-none-any.whl.metadata (108 kB)
Collecting typing-inspection>=0.4.2 (from fastapi>=0.116.0->terrayield-land-intelligence==0.1.0)
  Downloading typing_inspection-0.4.2-py3-none-any.whl.metadata (2.6 kB)
Collecting annotated-doc>=0.0.2 (from fastapi>=0.116.0->terrayield-land-intelligence==0.1.0)
  Downloading annotated_doc-0.0.4-py3-none-any.whl.metadata (6.6 kB)
Collecting packaging (from geoalchemy2>=0.16.0->terrayield-land-intelligence==0.1.0)
  Downloading packaging-26.2-py3-none-any.whl.metadata (3.5 kB)
Collecting numpy>=1.24 (from geopandas>=1.0.1->terrayield-land-intelligence==0.1.0)
  Downloading numpy-2.4.4-cp312-cp312-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl.metadata (6.6 kB)
Collecting anyio (from httpx>=0.28.0->terrayield-land-intelligence==0.1.0)
  Downloading anyio-4.13.0-py3-none-any.whl.metadata (4.5 kB)
Collecting certifi (from httpx>=0.28.0->terrayield-land-intelligence==0.1.0)
  Downloading certifi-2026.4.22-py3-none-any.whl.metadata (2.5 kB)
Collecting httpcore==1.* (from httpx>=0.28.0->terrayield-land-intelligence==0.1.0)
  Downloading httpcore-1.0.9-py3-none-any.whl.metadata (21 kB)
Collecting idna (from httpx>=0.28.0->terrayield-land-intelligence==0.1.0)
  Downloading idna-3.13-py3-none-any.whl.metadata (8.0 kB)
Collecting h11>=0.16 (from httpcore==1.*->httpx>=0.28.0->terrayield-land-intelligence==0.1.0)
  Downloading h11-0.16.0-py3-none-any.whl.metadata (8.3 kB)
Collecting psycopg-binary==3.3.4 (from psycopg[binary]>=3.2.0->terrayield-land-intelligence==0.1.0)
  Downloading psycopg_binary-3.3.4-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.whl.metadata (2.7 kB)
Collecting six>=1.5 (from python-dateutil>=2.9.0->terrayield-land-intelligence==0.1.0)
  Downloading six-1.17.0-py2.py3-none-any.whl.metadata (1.7 kB)
Collecting charset_normalizer<4,>=2 (from requests>=2.32.0->terrayield-land-intelligence==0.1.0)
  Downloading charset_normalizer-3.4.7-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.metadata (40 kB)
Collecting urllib3<3,>=1.26 (from requests>=2.32.0->terrayield-land-intelligence==0.1.0)
  Downloading urllib3-2.6.3-py3-none-any.whl.metadata (6.9 kB)
Collecting greenlet>=1 (from sqlalchemy>=2.0.38->terrayield-land-intelligence==0.1.0)
  Downloading greenlet-3.5.0-cp312-cp312-manylinux_2_24_x86_64.manylinux_2_28_x86_64.whl.metadata (3.7 kB)
Collecting click>=7.0 (from uvicorn>=0.34.0->uvicorn[standard]>=0.34.0->terrayield-land-intelligence==0.1.0)
  Downloading click-8.3.3-py3-none-any.whl.metadata (2.6 kB)
Collecting httptools>=0.6.3 (from uvicorn[standard]>=0.34.0->terrayield-land-intelligence==0.1.0)
  Downloading httptools-0.7.1-cp312-cp312-manylinux1_x86_64.manylinux_2_28_x86_64.manylinux_2_5_x86_64.whl.metadata (3.5 kB)
Collecting pyyaml>=5.1 (from uvicorn[standard]>=0.34.0->terrayield-land-intelligence==0.1.0)
  Downloading pyyaml-6.0.3-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.metadata (2.4 kB)
Collecting uvloop>=0.15.1 (from uvicorn[standard]>=0.34.0->terrayield-land-intelligence==0.1.0)
  Downloading uvloop-0.22.1-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.metadata (4.9 kB)
Collecting watchfiles>=0.20 (from uvicorn[standard]>=0.34.0->terrayield-land-intelligence==0.1.0)
  Downloading watchfiles-1.1.1-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (4.9 kB)
Collecting websockets>=10.4 (from uvicorn[standard]>=0.34.0->terrayield-land-intelligence==0.1.0)
  Downloading websockets-16.0-cp312-cp312-manylinux1_x86_64.manylinux_2_28_x86_64.manylinux_2_5_x86_64.whl.metadata (6.8 kB)
Collecting annotated-types>=0.6.0 (from pydantic>=2.9.0->fastapi>=0.116.0->terrayield-land-intelligence==0.1.0)
  Downloading annotated_types-0.7.0-py3-none-any.whl.metadata (15 kB)
Collecting pydantic-core==2.46.3 (from pydantic>=2.9.0->fastapi>=0.116.0->terrayield-land-intelligence==0.1.0)
  Downloading pydantic_core-2.46.3-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (6.6 kB)
Collecting MarkupSafe>=0.9.2 (from Mako->alembic>=1.14.1->terrayield-land-intelligence==0.1.0)
  Downloading markupsafe-3.0.3-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.metadata (2.7 kB)
Downloading alembic-1.18.4-py3-none-any.whl (263 kB)
Downloading fastapi-0.136.1-py3-none-any.whl (117 kB)
Downloading geoalchemy2-0.19.0-py3-none-any.whl (81 kB)
Downloading geopandas-1.1.3-py3-none-any.whl (342 kB)
Downloading httpx-0.28.1-py3-none-any.whl (73 kB)
Downloading httpcore-1.0.9-py3-none-any.whl (78 kB)
Downloading pandas-3.0.2-cp312-cp312-manylinux_2_24_x86_64.manylinux_2_28_x86_64.whl (10.9 MB)
   ÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöü 10.9/10.9 MB 4.7 MB/s eta 0:00:00
Downloading psycopg-3.3.4-py3-none-any.whl (213 kB)
Downloading psycopg_binary-3.3.4-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.whl (5.2 MB)
   ÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöü 5.2/5.2 MB 4.7 MB/s eta 0:00:00
Downloading pydantic_settings-2.14.0-py3-none-any.whl (60 kB)
Downloading pyogrio-0.12.1-cp312-cp312-manylinux_2_28_x86_64.whl (32.5 MB)
   ÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöü 32.5/32.5 MB 4.1 MB/s eta 0:00:00
Downloading pyproj-3.7.2-cp312-cp312-manylinux_2_28_x86_64.whl (9.6 MB)
   ÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöü 9.6/9.6 MB 4.1 MB/s eta 0:00:00
Downloading python_dateutil-2.9.0.post0-py2.py3-none-any.whl (229 kB)
Downloading python_dotenv-1.2.2-py3-none-any.whl (22 kB)
Downloading requests-2.33.1-py3-none-any.whl (64 kB)
Downloading shapely-2.1.2-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.whl (3.1 MB)
   ÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöü 3.1/3.1 MB 3.8 MB/s eta 0:00:00
Downloading sqlalchemy-2.0.49-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (3.4 MB)
   ÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöü 3.4/3.4 MB 3.9 MB/s eta 0:00:00
Downloading uvicorn-0.46.0-py3-none-any.whl (70 kB)
Downloading annotated_doc-0.0.4-py3-none-any.whl (5.3 kB)
Downloading certifi-2026.4.22-py3-none-any.whl (135 kB)
Downloading charset_normalizer-3.4.7-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (216 kB)
Downloading click-8.3.3-py3-none-any.whl (110 kB)
Downloading greenlet-3.5.0-cp312-cp312-manylinux_2_24_x86_64.manylinux_2_28_x86_64.whl (611 kB)
   ÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöü 611.4/611.4 kB 3.3 MB/s eta 0:00:00
Downloading h11-0.16.0-py3-none-any.whl (37 kB)
Downloading httptools-0.7.1-cp312-cp312-manylinux1_x86_64.manylinux_2_28_x86_64.manylinux_2_5_x86_64.whl (517 kB)
Downloading idna-3.13-py3-none-any.whl (68 kB)
Downloading numpy-2.4.4-cp312-cp312-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl (16.6 MB)
   ÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöü 16.6/16.6 MB 4.5 MB/s eta 0:00:00
Downloading pydantic-2.13.3-py3-none-any.whl (471 kB)
Downloading pydantic_core-2.46.3-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (2.1 MB)
   ÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöü 2.1/2.1 MB 4.4 MB/s eta 0:00:00
Downloading pyyaml-6.0.3-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (807 kB)
   ÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöü 807.9/807.9 kB 4.3 MB/s eta 0:00:00
Downloading six-1.17.0-py2.py3-none-any.whl (11 kB)
Downloading starlette-1.0.0-py3-none-any.whl (72 kB)
Downloading anyio-4.13.0-py3-none-any.whl (114 kB)
Downloading typing_extensions-4.15.0-py3-none-any.whl (44 kB)
Downloading typing_inspection-0.4.2-py3-none-any.whl (14 kB)
Downloading urllib3-2.6.3-py3-none-any.whl (131 kB)
Downloading uvloop-0.22.1-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (4.4 MB)
   ÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöü 4.4/4.4 MB 3.2 MB/s eta 0:00:00
Downloading watchfiles-1.1.1-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (456 kB)
Downloading websockets-16.0-cp312-cp312-manylinux1_x86_64.manylinux_2_28_x86_64.manylinux_2_5_x86_64.whl (184 kB)
Downloading mako-1.3.12-py3-none-any.whl (78 kB)
Downloading packaging-26.2-py3-none-any.whl (100 kB)
Downloading annotated_types-0.7.0-py3-none-any.whl (13 kB)
Downloading markupsafe-3.0.3-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (22 kB)
Building wheels for collected packages: terrayield-land-intelligence
  Building editable for terrayield-land-intelligence (pyproject.toml): started
  Building editable for terrayield-land-intelligence (pyproject.toml): finished with status 'done'
  Created wheel for terrayield-land-intelligence: filename=terrayield_land_intelligence-0.1.0-0.editable-py3-none-any.whl size=10071 sha256=550cbd43beb1566c6a5110b0695ab6096d0365cac9808069cd3c052a086410aa
  Stored in directory: /tmp/pip-ephem-wheel-cache-q6hcg_5v/wheels/54/1b/b7/aa63e25c8f14f4f2ae7b04e6097bdecb770e455c5c1ee0a600
Successfully built terrayield-land-intelligence
Installing collected packages: websockets, uvloop, urllib3, typing-extensions, six, pyyaml, python-dotenv, psycopg-binary, packaging, numpy, MarkupSafe, idna, httptools, h11, greenlet, click, charset_normalizer, certifi, annotated-types, annotated-doc, uvicorn, typing-inspection, sqlalchemy, shapely, requests, python-dateutil, pyproj, pyogrio, pydantic-core, psycopg, Mako, httpcore, anyio, watchfiles, starlette, pydantic, pandas, httpx, geoalchemy2, alembic, pydantic-settings, geopandas, fastapi, terrayield-land-intelligence
Successfully installed Mako-1.3.12 MarkupSafe-3.0.3 alembic-1.18.4 annotated-doc-0.0.4 annotated-types-0.7.0 anyio-4.13.0 certifi-2026.4.22 charset_normalizer-3.4.7 click-8.3.3 fastapi-0.136.1 geoalchemy2-0.19.0 geopandas-1.1.3 greenlet-3.5.0 h11-0.16.0 httpcore-1.0.9 httptools-0.7.1 httpx-0.28.1 idna-3.13 numpy-2.4.4 packaging-26.2 pandas-3.0.2 psycopg-3.3.4 psycopg-binary-3.3.4 pydantic-2.13.3 pydantic-core-2.46.3 pydantic-settings-2.14.0 pyogrio-0.12.1 pyproj-3.7.2 python-dateutil-2.9.0.post0 python-dotenv-1.2.2 pyyaml-6.0.3 requests-2.33.1 shapely-2.1.2 six-1.17.0 sqlalchemy-2.0.49 starlette-1.0.0 terrayield-land-intelligence-0.1.0 typing-extensions-4.15.0 typing-inspection-0.4.2 urllib3-2.6.3 uvicorn-0.46.0 uvloop-0.22.1 watchfiles-1.1.1 websockets-16.0
WARNING: Running pip as the 'root' user can result in broken permissions and conflicting behaviour with the system pack
age manager, possibly rendering your system unusable. It is recommended to use a virtual environment instead: https://p
ip.pypa.io/warnings/venv. Use the --root-user-action option if you know what you are doing and want to suppress this wa
rning.

[notice] A new release of pip is available: 25.0.1 -> 26.1
[notice] To update, run: pip install --upgrade pip
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Will assume transactional DDL.

[204 s] api dependency bootstrap and migration in one-shot container EXIT=0
docker :  Container terrayield_land_postgis Running 
At C:\Users\cagda\Documents\chat_gpt_clone_1\ai-task-scripts\terrayield_recovery_018_multitask_supervisor.ps1:155 char:
80
+ ... ontainer' { docker compose @ComposeArgs run --rm api sh -lc 'cd /app  ...
+                 ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : NotSpecified: ( Container terr...ostgis Running :String) [], RemoteException
    + FullyQualifiedErrorId : NativeCommandError
 
 Container terrayield_land_intelligence-api-run-30d3fa7d2509 Creating 
 Container terrayield_land_intelligence-api-run-30d3fa7d2509 Created 
Obtaining file:///app
  Installing build dependencies: started
  Installing build dependencies: finished with status 'done'
  Checking if build backend supports build_editable: started
  Checking if build backend supports build_editable: finished with status 'done'
  Getting requirements to build editable: started
  Getting requirements to build editable: finished with status 'done'
  Preparing editable metadata (pyproject.toml): started
  Preparing editable metadata (pyproject.toml): finished with status 'done'
Collecting alembic>=1.14.1 (from terrayield-land-intelligence==0.1.0)
  Downloading alembic-1.18.4-py3-none-any.whl.metadata (7.2 kB)
Collecting fastapi>=0.116.0 (from terrayield-land-intelligence==0.1.0)
  Downloading fastapi-0.136.1-py3-none-any.whl.metadata (28 kB)
Collecting geoalchemy2>=0.16.0 (from terrayield-land-intelligence==0.1.0)
  Downloading geoalchemy2-0.19.0-py3-none-any.whl.metadata (2.1 kB)
Collecting geopandas>=1.0.1 (from terrayield-land-intelligence==0.1.0)
  Downloading geopandas-1.1.3-py3-none-any.whl.metadata (2.3 kB)
Collecting httpx>=0.28.0 (from terrayield-land-intelligence==0.1.0)
  Downloading httpx-0.28.1-py3-none-any.whl.metadata (7.1 kB)
Collecting pandas>=2.2.3 (from terrayield-land-intelligence==0.1.0)
  Downloading pandas-3.0.2-cp312-cp312-manylinux_2_24_x86_64.manylinux_2_28_x86_64.whl.metadata (79 kB)
Collecting psycopg>=3.2.0 (from psycopg[binary]>=3.2.0->terrayield-land-intelligence==0.1.0)
  Downloading psycopg-3.3.4-py3-none-any.whl.metadata (4.3 kB)
Collecting pyproj>=3.7.1 (from terrayield-land-intelligence==0.1.0)
  Downloading pyproj-3.7.2-cp312-cp312-manylinux_2_28_x86_64.whl.metadata (31 kB)
Collecting pyogrio>=0.11.1 (from terrayield-land-intelligence==0.1.0)
  Downloading pyogrio-0.12.1-cp312-cp312-manylinux_2_28_x86_64.whl.metadata (5.9 kB)
Collecting pydantic-settings>=2.8.0 (from terrayield-land-intelligence==0.1.0)
  Downloading pydantic_settings-2.14.0-py3-none-any.whl.metadata (3.4 kB)
Collecting python-dateutil>=2.9.0 (from terrayield-land-intelligence==0.1.0)
  Downloading python_dateutil-2.9.0.post0-py2.py3-none-any.whl.metadata (8.4 kB)
Collecting python-dotenv>=1.0.1 (from terrayield-land-intelligence==0.1.0)
  Downloading python_dotenv-1.2.2-py3-none-any.whl.metadata (27 kB)
Collecting requests>=2.32.0 (from terrayield-land-intelligence==0.1.0)
  Downloading requests-2.33.1-py3-none-any.whl.metadata (4.8 kB)
Collecting shapely>=2.0.7 (from terrayield-land-intelligence==0.1.0)
  Downloading shapely-2.1.2-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.whl.metadata (6.8 kB)
Collecting sqlalchemy>=2.0.38 (from terrayield-land-intelligence==0.1.0)
  Downloading sqlalchemy-2.0.49-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.metadata (9.5 kB)
Collecting uvicorn>=0.34.0 (from uvicorn[standard]>=0.34.0->terrayield-land-intelligence==0.1.0)
  Downloading uvicorn-0.46.0-py3-none-any.whl.metadata (6.7 kB)
Collecting Mako (from alembic>=1.14.1->terrayield-land-intelligence==0.1.0)
  Downloading mako-1.3.12-py3-none-any.whl.metadata (2.9 kB)
Collecting typing-extensions>=4.12 (from alembic>=1.14.1->terrayield-land-intelligence==0.1.0)
  Downloading typing_extensions-4.15.0-py3-none-any.whl.metadata (3.3 kB)
Collecting starlette>=0.46.0 (from fastapi>=0.116.0->terrayield-land-intelligence==0.1.0)
  Downloading starlette-1.0.0-py3-none-any.whl.metadata (6.3 kB)
Collecting pydantic>=2.9.0 (from fastapi>=0.116.0->terrayield-land-intelligence==0.1.0)
  Downloading pydantic-2.13.3-py3-none-any.whl.metadata (108 kB)
Collecting typing-inspection>=0.4.2 (from fastapi>=0.116.0->terrayield-land-intelligence==0.1.0)
  Downloading typing_inspection-0.4.2-py3-none-any.whl.metadata (2.6 kB)
Collecting annotated-doc>=0.0.2 (from fastapi>=0.116.0->terrayield-land-intelligence==0.1.0)
  Downloading annotated_doc-0.0.4-py3-none-any.whl.metadata (6.6 kB)
Collecting packaging (from geoalchemy2>=0.16.0->terrayield-land-intelligence==0.1.0)
  Downloading packaging-26.2-py3-none-any.whl.metadata (3.5 kB)
Collecting numpy>=1.24 (from geopandas>=1.0.1->terrayield-land-intelligence==0.1.0)
  Downloading numpy-2.4.4-cp312-cp312-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl.metadata (6.6 kB)
Collecting anyio (from httpx>=0.28.0->terrayield-land-intelligence==0.1.0)
  Downloading anyio-4.13.0-py3-none-any.whl.metadata (4.5 kB)
Collecting certifi (from httpx>=0.28.0->terrayield-land-intelligence==0.1.0)
  Downloading certifi-2026.4.22-py3-none-any.whl.metadata (2.5 kB)
Collecting httpcore==1.* (from httpx>=0.28.0->terrayield-land-intelligence==0.1.0)
  Downloading httpcore-1.0.9-py3-none-any.whl.metadata (21 kB)
Collecting idna (from httpx>=0.28.0->terrayield-land-intelligence==0.1.0)
  Downloading idna-3.13-py3-none-any.whl.metadata (8.0 kB)
Collecting h11>=0.16 (from httpcore==1.*->httpx>=0.28.0->terrayield-land-intelligence==0.1.0)
  Downloading h11-0.16.0-py3-none-any.whl.metadata (8.3 kB)
Collecting psycopg-binary==3.3.4 (from psycopg[binary]>=3.2.0->terrayield-land-intelligence==0.1.0)
  Downloading psycopg_binary-3.3.4-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.whl.metadata (2.7 kB)
Collecting six>=1.5 (from python-dateutil>=2.9.0->terrayield-land-intelligence==0.1.0)
  Downloading six-1.17.0-py2.py3-none-any.whl.metadata (1.7 kB)
Collecting charset_normalizer<4,>=2 (from requests>=2.32.0->terrayield-land-intelligence==0.1.0)
  Downloading charset_normalizer-3.4.7-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.metadata (40 kB)
Collecting urllib3<3,>=1.26 (from requests>=2.32.0->terrayield-land-intelligence==0.1.0)
  Downloading urllib3-2.6.3-py3-none-any.whl.metadata (6.9 kB)
Collecting greenlet>=1 (from sqlalchemy>=2.0.38->terrayield-land-intelligence==0.1.0)
  Downloading greenlet-3.5.0-cp312-cp312-manylinux_2_24_x86_64.manylinux_2_28_x86_64.whl.metadata (3.7 kB)
Collecting click>=7.0 (from uvicorn>=0.34.0->uvicorn[standard]>=0.34.0->terrayield-land-intelligence==0.1.0)
  Downloading click-8.3.3-py3-none-any.whl.metadata (2.6 kB)
Collecting httptools>=0.6.3 (from uvicorn[standard]>=0.34.0->terrayield-land-intelligence==0.1.0)
  Downloading httptools-0.7.1-cp312-cp312-manylinux1_x86_64.manylinux_2_28_x86_64.manylinux_2_5_x86_64.whl.metadata (3.5 kB)
Collecting pyyaml>=5.1 (from uvicorn[standard]>=0.34.0->terrayield-land-intelligence==0.1.0)
  Downloading pyyaml-6.0.3-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.metadata (2.4 kB)
Collecting uvloop>=0.15.1 (from uvicorn[standard]>=0.34.0->terrayield-land-intelligence==0.1.0)
  Downloading uvloop-0.22.1-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.metadata (4.9 kB)
Collecting watchfiles>=0.20 (from uvicorn[standard]>=0.34.0->terrayield-land-intelligence==0.1.0)
  Downloading watchfiles-1.1.1-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (4.9 kB)
Collecting websockets>=10.4 (from uvicorn[standard]>=0.34.0->terrayield-land-intelligence==0.1.0)
  Downloading websockets-16.0-cp312-cp312-manylinux1_x86_64.manylinux_2_28_x86_64.manylinux_2_5_x86_64.whl.metadata (6.8 kB)
Collecting annotated-types>=0.6.0 (from pydantic>=2.9.0->fastapi>=0.116.0->terrayield-land-intelligence==0.1.0)
  Downloading annotated_types-0.7.0-py3-none-any.whl.metadata (15 kB)
Collecting pydantic-core==2.46.3 (from pydantic>=2.9.0->fastapi>=0.116.0->terrayield-land-intelligence==0.1.0)
  Downloading pydantic_core-2.46.3-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (6.6 kB)
Collecting MarkupSafe>=0.9.2 (from Mako->alembic>=1.14.1->terrayield-land-intelligence==0.1.0)
  Downloading markupsafe-3.0.3-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.metadata (2.7 kB)
Downloading alembic-1.18.4-py3-none-any.whl (263 kB)
Downloading fastapi-0.136.1-py3-none-any.whl (117 kB)
Downloading geoalchemy2-0.19.0-py3-none-any.whl (81 kB)
Downloading geopandas-1.1.3-py3-none-any.whl (342 kB)
Downloading httpx-0.28.1-py3-none-any.whl (73 kB)
Downloading httpcore-1.0.9-py3-none-any.whl (78 kB)
Downloading pandas-3.0.2-cp312-cp312-manylinux_2_24_x86_64.manylinux_2_28_x86_64.whl (10.9 MB)
   ÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöü 10.9/10.9 MB 4.7 MB/s eta 0:00:00
Downloading psycopg-3.3.4-py3-none-any.whl (213 kB)
Downloading psycopg_binary-3.3.4-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.whl (5.2 MB)
   ÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöü 5.2/5.2 MB 4.7 MB/s eta 0:00:00
Downloading pydantic_settings-2.14.0-py3-none-any.whl (60 kB)
Downloading pyogrio-0.12.1-cp312-cp312-manylinux_2_28_x86_64.whl (32.5 MB)
   ÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöü 32.5/32.5 MB 4.1 MB/s eta 0:00:00
Downloading pyproj-3.7.2-cp312-cp312-manylinux_2_28_x86_64.whl (9.6 MB)
   ÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöü 9.6/9.6 MB 4.1 MB/s eta 0:00:00
Downloading python_dateutil-2.9.0.post0-py2.py3-none-any.whl (229 kB)
Downloading python_dotenv-1.2.2-py3-none-any.whl (22 kB)
Downloading requests-2.33.1-py3-none-any.whl (64 kB)
Downloading shapely-2.1.2-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.whl (3.1 MB)
   ÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöü 3.1/3.1 MB 3.8 MB/s eta 0:00:00
Downloading sqlalchemy-2.0.49-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (3.4 MB)
   ÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöü 3.4/3.4 MB 3.9 MB/s eta 0:00:00
Downloading uvicorn-0.46.0-py3-none-any.whl (70 kB)
Downloading annotated_doc-0.0.4-py3-none-any.whl (5.3 kB)
Downloading certifi-2026.4.22-py3-none-any.whl (135 kB)
Downloading charset_normalizer-3.4.7-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (216 kB)
Downloading click-8.3.3-py3-none-any.whl (110 kB)
Downloading greenlet-3.5.0-cp312-cp312-manylinux_2_24_x86_64.manylinux_2_28_x86_64.whl (611 kB)
   ÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöü 611.4/611.4 kB 3.3 MB/s eta 0:00:00
Downloading h11-0.16.0-py3-none-any.whl (37 kB)
Downloading httptools-0.7.1-cp312-cp312-manylinux1_x86_64.manylinux_2_28_x86_64.manylinux_2_5_x86_64.whl (517 kB)
Downloading idna-3.13-py3-none-any.whl (68 kB)
Downloading numpy-2.4.4-cp312-cp312-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl (16.6 MB)
   ÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöü 16.6/16.6 MB 4.5 MB/s eta 0:00:00
Downloading pydantic-2.13.3-py3-none-any.whl (471 kB)
Downloading pydantic_core-2.46.3-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (2.1 MB)
   ÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöü 2.1/2.1 MB 4.4 MB/s eta 0:00:00
Downloading pyyaml-6.0.3-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (807 kB)
   ÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöü 807.9/807.9 kB 4.3 MB/s eta 0:00:00
Downloading six-1.17.0-py2.py3-none-any.whl (11 kB)
Downloading starlette-1.0.0-py3-none-any.whl (72 kB)
Downloading anyio-4.13.0-py3-none-any.whl (114 kB)
Downloading typing_extensions-4.15.0-py3-none-any.whl (44 kB)
Downloading typing_inspection-0.4.2-py3-none-any.whl (14 kB)
Downloading urllib3-2.6.3-py3-none-any.whl (131 kB)
Downloading uvloop-0.22.1-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (4.4 MB)
   ÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöüÔöü 4.4/4.4 MB 3.2 MB/s eta 0:00:00
Downloading watchfiles-1.1.1-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (456 kB)
Downloading websockets-16.0-cp312-cp312-manylinux1_x86_64.manylinux_2_28_x86_64.manylinux_2_5_x86_64.whl (184 kB)
Downloading mako-1.3.12-py3-none-any.whl (78 kB)
Downloading packaging-26.2-py3-none-any.whl (100 kB)
Downloading annotated_types-0.7.0-py3-none-any.whl (13 kB)
Downloading markupsafe-3.0.3-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (22 kB)
Building wheels for collected packages: terrayield-land-intelligence
  Building editable for terrayield-land-intelligence (pyproject.toml): started
  Building editable for terrayield-land-intelligence (pyproject.toml): finished with status 'done'
  Created wheel for terrayield-land-intelligence: filename=terrayield_land_intelligence-0.1.0-0.editable-py3-none-any.whl size=10071 sha256=550cbd43beb1566c6a5110b0695ab6096d0365cac9808069cd3c052a086410aa
  Stored in directory: /tmp/pip-ephem-wheel-cache-q6hcg_5v/wheels/54/1b/b7/aa63e25c8f14f4f2ae7b04e6097bdecb770e455c5c1ee0a600
Successfully built terrayield-land-intelligence
Installing collected packages: websockets, uvloop, urllib3, typing-extensions, six, pyyaml, python-dotenv, psycopg-binary, packaging, numpy, MarkupSafe, idna, httptools, h11, greenlet, click, charset_normalizer, certifi, annotated-types, annotated-doc, uvicorn, typing-inspection, sqlalchemy, shapely, requests, python-dateutil, pyproj, pyogrio, pydantic-core, psycopg, Mako, httpcore, anyio, watchfiles, starlette, pydantic, pandas, httpx, geoalchemy2, alembic, pydantic-settings, geopandas, fastapi, terrayield-land-intelligence
Successfully installed Mako-1.3.12 MarkupSafe-3.0.3 alembic-1.18.4 annotated-doc-0.0.4 annotated-types-0.7.0 anyio-4.13.0 certifi-2026.4.22 charset_normalizer-3.4.7 click-8.3.3 fastapi-0.136.1 geoalchemy2-0.19.0 geopandas-1.1.3 greenlet-3.5.0 h11-0.16.0 httpcore-1.0.9 httptools-0.7.1 httpx-0.28.1 idna-3.13 numpy-2.4.4 packaging-26.2 pandas-3.0.2 psycopg-3.3.4 psycopg-binary-3.3.4 pydantic-2.13.3 pydantic-core-2.46.3 pydantic-settings-2.14.0 pyogrio-0.12.1 pyproj-3.7.2 python-dateutil-2.9.0.post0 python-dotenv-1.2.2 pyyaml-6.0.3 requests-2.33.1 shapely-2.1.2 six-1.17.0 sqlalchemy-2.0.49 starlette-1.0.0 terrayield-land-intelligence-0.1.0 typing-extensions-4.15.0 typing-inspection-0.4.2 urllib3-2.6.3 uvicorn-0.46.0 uvloop-0.22.1 watchfiles-1.1.1 websockets-16.0
WARNING: Running pip as the 'root' user can result in broken permissions and conflicting behaviour with the system pack
age manager, possibly rendering your system unusable. It is recommended to use a virtual environment instead: https://p
ip.pypa.io/warnings/venv. Use the --root-user-action option if you know what you are doing and want to suppress this wa
rning.

[notice] A new release of pip is available: 25.0.1 -> 26.1
[notice] To update, run: pip install --upgrade pip
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Will assume transactional DDL.

[204 s] --- start api with corrected command override ---
docker :  Container terrayield_land_postgis Running 
At C:\Users\cagda\Documents\chat_gpt_clone_1\ai-task-scripts\terrayield_recovery_018_multitask_supervisor.ps1:156 char:
61
+ ... corrected command override' { docker compose @ComposeArgs up -d api }
+                                   ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : NotSpecified: ( Container terr...ostgis Running :String) [], RemoteException
    + FullyQualifiedErrorId : NativeCommandError
 
 Container terrayield_land_api Creating 
 Container terrayield_land_api Created 
 Container terrayield_land_api Starting 
 Container terrayield_land_api Started 

[205 s] start api with corrected command override EXIT=0
docker :  Container terrayield_land_postgis Running 
At C:\Users\cagda\Documents\chat_gpt_clone_1\ai-task-scripts\terrayield_recovery_018_multitask_supervisor.ps1:156 char:
61
+ ... corrected command override' { docker compose @ComposeArgs up -d api }
+                                   ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : NotSpecified: ( Container terr...ostgis Running :String) [], RemoteException
    + FullyQualifiedErrorId : NativeCommandError
 
 Container terrayield_land_api Creating 
 Container terrayield_land_api Created 
 Container terrayield_land_api Starting 
 Container terrayield_land_api Started 

SUMMARY_FILE=C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\.aays_next_fix\recovery_018_multitask_supervisor_20260504_003925\summary.md
DETAIL_FILE=C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\.aays_next_fix\recovery_018_multitask_supervisor_20260504_003925\detail.txt
OVERRIDE_FILE=C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\docker-compose.aays-api-command.yml
RESULT=healthy_or_recovered
API_READY=[236 s] WAIT_API attempt=6 [266 s] WAIT_API attempt=12 [292 s] API_HEALTH_READY attempt=18 True
RECOVERY_ACTION=write_override_bootstrap_migrate_restart_api
ELAPSED_SECONDS=297
RECOVERY_018_MULTITASK_SUPERVISOR_DONE

``

## Error
``text

``

