# Paths and Outputs

## Repo icindeki mevcut yollar

- repo root:
  - `C:\Users\cagda\Documents\GitHub\AAYS`
- page root:
  - `C:\Users\cagda\Documents\GitHub\AAYS\docs\chatgpt_status\internet_access_parcel_layer_low_credit_20260612`
- current runtime audit:
  - `C:\Users\cagda\Documents\GitHub\AAYS\docs\chatgpt_status\internet_access_parcel_layer_low_credit_20260612\reports\codex_internet_runtime_audit_20260623_1220.md`

## Mevcut eski agir paket

- root:
  - `F:\chatgpt\AAYS_WORK\internet_access_score10_real_build_20260610`
- processed:
  - `F:\chatgpt\AAYS_WORK\internet_access_score10_real_build_20260610\processed\parcel_internet_access_scores.geojson`
  - `F:\chatgpt\AAYS_WORK\internet_access_score10_real_build_20260610\processed\parcel_internet_access_scores.csv`
  - `F:\chatgpt\AAYS_WORK\internet_access_score10_real_build_20260610\processed\parcel_internet_access_factor_breakdown.csv`
- manifest:
  - `F:\chatgpt\AAYS_WORK\internet_access_score10_real_build_20260610\manifests\calculation_manifest.json`

## Onerilen yeni agir final root

- primary:
  - `F:\chatgpt\AAYS_WORK\internet_access_parcel_final_20260623`
- fallback:
  - `D:\AAYS_WORK\internet_access_parcel_final_20260623`

## Onerilen klasor yapisi

- `raw\`
- `processed\`
- `manifests\`
- `reports\`
- `exports\`
- `scripts\`
- `chatgpt_inbox\`
- `tmp\`

## Finalde beklenen dosyalar

- `processed\parcel_internet_access_scores.geojson`
  - renderable geometry icermeli
- `processed\parcel_internet_access_scores.csv`
  - parcel_id bazli olmali
- `processed\parcel_internet_access_factor_breakdown.csv`
  - factor table contract alanlarini icermeli
- `manifests\parcel_internet_access_manifest.json`
  - source, matching, confidence, geometry policy bilgilerini icermeli
- `reports\internet_access_parcel_final_validation.md`
  - final smoke ve gap kapanis raporu

## Repo icinde guncellenecek veya beslenecek alanlar

- `england_map_web\data\parcel_internet_access_scores.geojson`
  - yalnizca renderable fallback artifact varsa
- `england_map_web\internet_access_overlay.js`
- `england_map_web\app.js`
- `terrayield_land_intelligence\app\api\routes\map_layers.py`

## Son kabulte zorunlu endpoint

- `http://127.0.0.1:8010/map/internet-access?...`
  - bos degil
  - parcel geometry donmeli
