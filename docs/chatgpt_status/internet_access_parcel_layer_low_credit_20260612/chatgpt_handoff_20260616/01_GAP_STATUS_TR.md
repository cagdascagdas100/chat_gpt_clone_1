# Internet Layer Gap Status

Tarih: 2026-06-16

## P0 - Parcel Geometry Yok

- Durum: acik eksik
- Kanit:
  - `F:\chatgpt\AAYS_WORK\internet_access_score10_real_build_20260610\processed\parcel_internet_access_scores.geojson`
  - `feature_count = 50000`
  - `geometry_types = {None: 50000}`
- Etki:
  - haritada parcel thematic layer cizilemez
- Kapatma kosulu:
  - parcel polygon veya renderable geometry ile yeni ready GeoJSON/DB output

## P0 - Paket Production Parcel Layer Degil

- Durum: acik eksik
- Kanit:
  - `calculation_manifest.json`
  - `status=PROCESSED_PACKAGE_READY_POSTCODE_LEVEL_OFFICIAL_SOURCE`
  - `geometry_policy=null geometry only; no fake coordinates`
  - `db_write=false`
  - `production_deploy=false`
- Etki:
  - ChatGPT handoff "tamam" dense bile canli parcel layer tamam kabul edilemez
- Kapatma kosulu:
  - parcel-ready cikti + import-ready veya fallback-ready artifact

## P1 - Repo Fallback Dosyasi Eksik

- Durum: acik eksik
- Kanit:
  - `england_map_web/data/parcel_internet_access_scores.geojson` yok
- Etki:
  - DB yokken frontend fallback ile katman gosterilemez
- Kapatma kosulu:
  - renderable geometry iceren fallback dosyasi veya baska fail-soft source

## P1 - Popup / Right Panel Sozlesmesi Kismi

- Durum: acik eksik
- Mevcut:
  - skor
  - yuzde
  - seviye
  - confidence
  - kaynak
  - source_url
  - last_verified
- Eksik:
  - factor table
  - color category
  - source list
  - matching method
  - calculation explanation
  - right-side parcel detail binding
- Kapatma kosulu:
  - output contract alanlari eksiksiz gorunmeli

## P1 - Faktor Breakdown Veri Sozlesmesi Eksik

- Durum: acik eksik
- Kanit:
  - `parcel_internet_access_factor_breakdown.csv` header:
    - `source_unit_id`
    - `parcel_id`
    - `source_unit_type`
    - `source_dataset`
    - `source_file`
    - `fake_data`
- Etki:
  - istenen measured value / contribution / individual confidence tablo yapisi yok
- Kapatma kosulu:
  - factor breakdown ready dosyasi veya factor JSON array

## P1 - F/D ve E Storage Sozlesmesi Ayrik

- Durum: acik eksik
- Mevcut agir paket:
  - `F:\chatgpt\AAYS_WORK\internet_access_score10_real_build_20260610\...`
- Beklenen kalici final root:
  - bu handoff icin `F:\AAYS_WORK\internet_access_final_20260616\...`
  - alternatif `D:\AAYS_WORK\internet_access_final_20260616\...`
- Etki:
  - final artifact lokasyonu net degil
- Kapatma kosulu:
  - final outputs tek agir root altinda duzenli

## P2 - Open-only Launcher Stabil Degil

- Durum: acik eksik ama parcel-layer veri eksiginden ikincil
- Mevcut:
  - foreground `uvicorn` ile uygulama aciliyor
  - helper launcher kararsiz
- Codex tarafinda yapilan:
  - route fail-soft patch
  - health fail-soft patch
  - launcher script iyilestirme denemesi
- Kapatma kosulu:
  - helper script kararliligi veya net local runbook

## Kisa Hukum

- report chain completion: tamam
- parcel internet layer completion: tamam degil
- ana blocker: parcel-level renderable geometry yok

