# PowerShell Runbook - Distance to Nearby Property Types

Bu runbook, Codex harcamadan local dogrulamayi senin yapman icin yazildi.

## 1) D/F koklerini hazirla

Repo root icinden:

```powershell
powershell -ExecutionPolicy Bypass -File .\docs\chatgpt_status\AAYS_REAL_TOPOGRAPHY_PRODUCT\chatgpt_distance_property_types_handoff_20260623\scripts\10_prepare_df_roots.ps1
```

## 2) Runtime probe raporu uret

```powershell
powershell -ExecutionPolicy Bypass -File .\docs\chatgpt_status\AAYS_REAL_TOPOGRAPHY_PRODUCT\chatgpt_distance_property_types_handoff_20260623\scripts\20_distance_property_types_runtime_probe.ps1
```

Bu script su kontrolleri yapar:

- `.env` icindeki `TYLI_DB_PORT` ve `TYLI_DATABASE_URL`
- Local port probe (`55460`, `55432`, `55537`, `5432`)
- `docker ps -a`
- `/health`
- `/map/distance-property-types?...`
- Feature count

Rapor varsayilan olarak su klasore yazar:

- `D:\AAYS_DATA\distance_property_types_page34_20260623\reports\`

## 3) Docker / PostGIS kapaliysa

Once Docker Desktop'i manual ac.

Ardindan:

```powershell
Set-Location C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence
docker compose up -d db
docker compose ps
docker exec terrayield_land_postgis pg_isready -U postgres -d terrayield_land
```

## 4) API gerekiyorsa yeniden baslat

```powershell
Set-Location C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence
powershell -ExecutionPolicy Bypass -File .\start_uvicorn_8010_bg.ps1
```

Sonra tekrar:

```powershell
Invoke-WebRequest http://127.0.0.1:8010/health -UseBasicParsing | Select-Object -ExpandProperty Content
Invoke-WebRequest "http://127.0.0.1:8010/map/distance-property-types?bbox=-0.55,51.28,0.35,51.75&limit=10" -UseBasicParsing | Select-Object -ExpandProperty Content
```

## 5) Shared runner zincirini ancak gerekirse elle kontrol et

Bu katman icin ilk kritik konu DB runtime'dir. Shared runner ancak DB duzeldikten sonra anlami olur.

Kontrol edilirse:

```powershell
Get-Content C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-tasks\current-task.json
Get-Content C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-heartbeat\portable-runner.md
```

## 6) ChatGPT'ye gonderilecekler

Asagidakileri birlikte yukle:

1. Bu handoff klasoru veya ZIP'i
2. `D:\AAYS_DATA\distance_property_types_page34_20260623\reports\` altindaki son probe raporu
3. Gerekirse:
   - `terrayield_land_intelligence\.env`
   - `terrayield_land_intelligence\docker-compose.yml`
   - `docs\chatgpt_status\AAYS_REAL_TOPOGRAPHY_PRODUCT\reports\codex_distance_property_types_integration_20260617_02.md`
   - `docs\chatgpt_status\AAYS_REAL_TOPOGRAPHY_PRODUCT\reports\page34_runtime_wrapper_probe_20260623_153149.md`

## 7) Gercek kabul

Su komut ciktisinda bos olmayan `features` gorulmeden bu layer tamam degildir:

```powershell
Invoke-WebRequest "http://127.0.0.1:8010/map/distance-property-types?bbox=-0.55,51.28,0.35,51.75&limit=10" -UseBasicParsing | Select-Object -ExpandProperty Content
```
