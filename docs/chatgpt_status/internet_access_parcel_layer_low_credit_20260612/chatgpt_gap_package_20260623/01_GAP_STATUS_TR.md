# Internet Layer Gap Status

Tarih: `2026-06-23`

## P0 - Parcel Geometry Yok

- kanit:
  - `F:\chatgpt\AAYS_WORK\internet_access_score10_real_build_20260610\processed\parcel_internet_access_scores.geojson`
  - geometry alanlari `null`
- etki:
  - thematic parcel map cizilemez
- kapanma kosulu:
  - gercek parcel polygon veya baska renderable geometry ile yeni output

## P0 - Paket Postcode-Level, Parcel-Level Degil

- kanit:
  - `F:\chatgpt\AAYS_WORK\internet_access_score10_real_build_20260610\manifests\calculation_manifest.json`
  - `status=PROCESSED_PACKAGE_READY_POSTCODE_LEVEL_OFFICIAL_SOURCE`
  - `geometry_policy=null geometry only; no fake coordinates`
- etki:
  - "report final" olsa da urun tamam kabul edilemez
- kapanma kosulu:
  - parcel_id bazli, renderable geometry iceren yeni dataset

## P1 - Repo Fallback Dosyasi Eksik

- kanit:
  - `C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\data\parcel_internet_access_scores.geojson` yok
- etki:
  - DB yokken frontend fallback calismaz
- kapanma kosulu:
  - geometri iceren fallback GeoJSON veya net baska fail-soft source

## P1 - Popup / Right Panel Sozlesmesi Eksik

- mevcut:
  - skor
  - yuzde
  - seviye
  - confidence
  - kaynak
  - source_url
  - last_verified
- eksik:
  - factor table
  - color category
  - source list
  - matching method
  - calculation explanation
  - right-side detail panel binding

## P1 - Factor Breakdown Veri Sozlesmesi Eksik

- kanit:
  - `parcel_internet_access_factor_breakdown.csv`
  - header sadece:
    - `source_unit_id`
    - `parcel_id`
    - `source_unit_type`
    - `source_dataset`
    - `source_file`
    - `fake_data`
- etki:
  - istenen measured value / contribution / confidence tablosu kurulamaz

## P1 - DB Tarafinda Parcel-Ready Import Kaniti Yok

- mevcut:
  - `/map/internet-access` 200 donuyor
  - ama bos feature collection donuyor
- etki:
  - ya tablo bos, ya import yok, ya geometry join yok

## P2 - Storage Root Daginik

- mevcut eski agir root:
  - `F:\chatgpt\AAYS_WORK\internet_access_score10_real_build_20260610`
- onerilen yeni final root:
  - `F:\chatgpt\AAYS_WORK\internet_access_parcel_final_20260623`
- fallback:
  - `D:\AAYS_WORK\internet_access_parcel_final_20260623`

## P2 - Helper Launcher Ikincil Risk

- uygulama aciliyor
- ama helper stability konusu ikincil
- ana problem veri/geometry

## Duzeltilmis ama geri alinmamasi gerekenler

1. `terrayield_land_intelligence/app/schemas/contractor.py`
   - eksik response modeli eklendi
2. `england_map_web/internet_access_overlay.js`
   - Internet layer artik varsayilan olarak `sales-history` proxy fallback kullanmiyor

Bunlari geri alma.
