# Internet Access Parcel Layer Open Smoke

- date_local: 2026-06-16 15:18 Europe/Istanbul
- repo: `cagdascagdas100/chat_gpt_clone_1`
- branch: `feature/terrayield-aays-integration`
- page_key: `internet_access_parcel_layer_low_credit_20260612`
- zip: `C:\Users\cagda\Downloads\codex_handoff_internet_access_final_20260616.zip`
- zip_sha256_match: `true`

## Report Chain Verification

- `docs/chatgpt_status/reports/ia106.json`
  - status: `READY_FOR_105`
  - completion_percent: `99`
  - runner_produced: `false`
  - operator_authorized_github_write: `true`
- `docs/chatgpt_status/reports/internet-access-105-shared-runner-package-and-validate.json`
  - status: `READY_FOR_107`
  - completion_percent: `99`
  - runner_produced: `false`
  - operator_authorized_github_write: `true`
- `docs/chatgpt_status/reports/internet-access-107-final-ready-gate.json`
  - status: `FINAL_READY`
  - completion_percent: `100`
  - runner_produced: `false`
  - operator_authorized_github_write: `true`

Result: report chain is internally consistent. This finalization is operator-authorized GitHub write, not runner-produced output.

## Local Evidence Restore

The following files were missing locally and were restored from ZIP evidence without changing page key or branch:

- `docs/chatgpt_status/reports/ia106.json`
- `docs/chatgpt_status/reports/internet-access-105-shared-runner-package-and-validate.json`
- `docs/chatgpt_status/reports/internet-access-107-final-ready-gate.json`
- `docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/automation/ia105_safe_progress.ps1`
- `docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/automation/ia106_safe_progress.ps1`
- `docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/automation/ia107_safe_final.ps1`

## Runtime Discovery

Detected repo-native open paths:

- `terrayield_land_intelligence/docker-compose.yml`
  - `db` service: PostGIS on host port `${TYLI_DB_PORT:-55432}`
  - `api` service: `uvicorn app.main:app --host 0.0.0.0 --port 8010`
- `terrayield_land_intelligence/README.md`
  - `docker compose up -d db`
  - `uvicorn app.main:app --reload --host 0.0.0.0 --port 8010`
- local helper scripts:
  - `terrayield_land_intelligence/start_open_only_8010.ps1`
  - `terrayield_land_intelligence/start_uvicorn_8010_bg.ps1`
  - `terrayield_land_intelligence/run_uvicorn_8010.ps1`

## Environment Gate

- Docker daemon: unavailable
  - `com.docker.service` status: `Stopped`
  - local start attempt from Codex shell: `Access denied`
- WSL state: unavailable for Docker Desktop
  - `wsl -l -v` returned no installed distribution
- DB ports observed closed during this smoke:
  - `55432`
  - `55537`
  - `55460`

This means live PostGIS-backed parcel data was not available during the Codex smoke run.

## Minimal Fail-Soft Fix Applied

To keep the page openable when DB is unavailable, two narrow route fixes were applied:

- `terrayield_land_intelligence/app/api/routes/map_layers.py`
  - `/map/internet-access` now checks DB socket availability before opening a DB connection.
  - offline behavior: immediate empty `FeatureCollection` instead of hanging until timeout.
- `terrayield_land_intelligence/app/api/routes/health.py`
  - `/health` now checks DB socket availability before `SELECT 1`.
  - offline behavior: immediate `database=degraded` instead of hanging until timeout.

Validation after patch:

- `python -m py_compile terrayield_land_intelligence/app/api/routes/map_layers.py terrayield_land_intelligence/app/api/routes/health.py` -> OK
- `node --check england_map_web/app.js` -> OK

## UI / Endpoint Smoke

Reliable foreground command used for smoke:

```powershell
$env:TYLI_DB_PORT='55460'
$env:TYLI_DATABASE_URL='postgresql+psycopg://postgres:postgres@localhost:55460/terrayield_land?connect_timeout=1'
Set-Location 'C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
C:\Python312\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8010
```

Observed while server was running:

- `GET /england_map_web/` -> `200 OK`
- `GET /health` -> `200 OK`
  - response:
    - `status=ok`
    - `database=degraded`
- `GET /map/internet-access?bbox=-0.16,51.48,-0.14,51.50&limit=5` -> `200 OK`
  - response:
    - `{"type":"FeatureCollection","features":[]}`

Meaning:

- app shell opens
- health endpoint responds without hanging
- Internet Access layer endpoint responds without hanging
- because DB is unavailable, the layer returns an empty collection in fail-soft mode

## Frontend Marker Verification

Verified in repo:

- `england_map_web/app.js`
  - internet icon asset: `./assets/icons/terrayield_icons/internet.png`
  - runtime loader: `./internet_access_overlay.js?v=20260525-internet-layer-v1`
- `england_map_web/index.html`
  - includes `internet_access_overlay.js`
- `england_map_web/internet_access_overlay.js`
  - default endpoint: `/map/internet-access`
  - popup fields include score, percent, level, confidence, factor, source, source URL, and last verified
- `terrayield_land_intelligence/app/api/routes/map_layers.py`
  - backend route: `GET /map/internet-access`

## Launcher Note

`start_open_only_8010.ps1` showed a brief initial listener on `127.0.0.1:8010`, but it was not stable under the Codex shell harness. The reliable open path in this environment was the direct foreground `uvicorn` command above. This report does not treat the unstable helper behavior as a code-completeness signal.

## Final Status

- page_final_report_status: `FINAL_READY`
- page_completion_percent: `100`
- app_open_status: `OPENABLE_WITH_FAIL_SOFT_FOREGROUND_COMMAND`
- internet_access_runtime_status: `FAIL_SOFT_OK_DB_GATE_BLOCKED`
- live_data_visible_in_this_smoke: `false`
- reason: `PostGIS/Docker unavailable in current machine state`

Conclusion: the Internet Access handoff/report chain is final-ready and correctly marked as operator-authorized GitHub write. In the current local environment, the application opens and the Internet Access endpoint now fails soft correctly, but parcel data remains gated by unavailable DB infrastructure.

## Completeness Audit Addendum

After the initial smoke, the packaged Internet Access dataset and frontend contract were audited against the original parcel-layer acceptance.

### What exists

- External processed package exists on `F:`:
  - `F:\chatgpt\AAYS_WORK\internet_access_score10_real_build_20260610\processed\parcel_internet_access_scores.csv`
  - `F:\chatgpt\AAYS_WORK\internet_access_score10_real_build_20260610\processed\parcel_internet_access_scores.geojson`
  - `F:\chatgpt\AAYS_WORK\internet_access_score10_real_build_20260610\processed\parcel_internet_access_factor_breakdown.csv`
  - `F:\chatgpt\AAYS_WORK\internet_access_score10_real_build_20260610\reports\internet_access_parcel_report.xlsx`
- Frontend marker exists:
  - `england_map_web/app.js` internet toggle
  - `england_map_web/internet_access_overlay.js` runtime bridge
  - backend `GET /map/internet-access`

### What blocks the layer from being "fully complete"

1. Packaged data is not parcel-geometry-ready
   - `parcel_internet_access_scores.geojson` contains `50000` features
   - geometry type distribution: `{None: 50000}`
   - result: every feature has `geometry: null`
   - this cannot render as a thematic parcel layer

2. Packaged data is postcode-level, not parcel-polygon level
   - `calculation_manifest.json`:
     - `status=PROCESSED_PACKAGE_READY_POSTCODE_LEVEL_OFFICIAL_SOURCE`
     - `geometry_policy=null geometry only; no fake coordinates`
     - `db_write=false`
     - `production_deploy=false`
   - result: the package is an official-source processed package, but not a production parcel map deployment package

3. Repo fallback file is still missing
   - `england_map_web/data/parcel_internet_access_scores.geojson` does not exist in repo
   - result: frontend fallback path is not connected to the packaged output

4. Factor breakdown contract is not fully implemented
   - `parcel_internet_access_factor_breakdown.csv` headers are only:
     - `source_unit_id`
     - `parcel_id`
     - `source_unit_type`
     - `source_dataset`
     - `source_file`
     - `fake_data`
   - result: the package does not provide the rich per-factor popup table requested by the original acceptance text

5. Popup/detail contract is partial
   - current popup shows score, percent, level, confidence, factor, source, source URL, last verified
   - current code does not show:
     - color category field
     - full factor table with measured value / contribution / source / individual confidence
     - explicit matching method
     - calculation explanation in the requested table form
     - right-side parcel detail panel binding specific to Internet Access

6. Storage root mismatch
   - original requirement asked for `E:\AAYS_DATA\internet_access\...`
   - verified package is currently on `F:\chatgpt\AAYS_WORK\internet_access_score10_real_build_20260610\...`
   - `E:\AAYS_DATA\internet_access\...` was absent in this smoke

### Judgment

The ChatGPT package is not fake and not empty, but it is not a 100% completed parcel-level Internet Access layer.

Accurate status:

- report-chain completion: `100%`
- live parcel-layer completion: `not complete`
- main blocker: `postcode-level official source package with null geometry, not parcel polygon output`

### Narrow code fixes applied in this Codex run

- `/map/internet-access` fail-soft DB gate added
- `/health` fail-soft DB gate added
- `england_map_web/internet_access_overlay.js` now rejects feature collections that have rows but no renderable geometry, so postcode/null-geometry packages are not misread as a valid visible layer

### Remaining work required for true completion

1. Convert the official source package into parcel-linked geometry output
   - real parcel polygons or valid parcel/area geometry
   - no null-geometry-only publish artifact
2. Write/import into:
   - `parcel_internet_access_scores` parcel-ready table
   - optional factor-detail store (`parcel_internet_access_factors` or equivalent JSON detail)
3. Connect repo fallback artifact:
   - `england_map_web/data/parcel_internet_access_scores.geojson`
4. Add right-side panel/detail binding for Internet Access factor table
5. Move or mirror final outputs into the requested durable root:
   - `E:\AAYS_DATA\internet_access\...`
