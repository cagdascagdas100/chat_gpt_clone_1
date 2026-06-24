# CHATGPT MASTER PROMPT - Internet Access Parcel Layer Gap Closure

Bu promptu ChatGPT'ye aynen ver.

## Sabit kapsam

Repo:
`cagdascagdas100/chat_gpt_clone_1`

Branch:
`feature/terrayield-aays-integration`

Page key:
`internet_access_parcel_layer_low_credit_20260612`

Local repo root:
`C:\Users\cagda\Documents\GitHub\AAYS`

Agir local output root:
`F:\chatgpt\AAYS_WORK\internet_access_parcel_final_20260623`

Fallback agir root:
`D:\AAYS_WORK\internet_access_parcel_final_20260623`

Baska page key, baska branch veya baska repo varsayma.

## Onceden dogrulanmis gercekler

1. Report chain final:
   - `docs/chatgpt_status/reports/ia106.json`
   - `docs/chatgpt_status/reports/internet-access-105-shared-runner-package-and-validate.json`
   - `docs/chatgpt_status/reports/internet-access-107-final-ready-gate.json`

2. App open blocker fix yapildi:
   - `terrayield_land_intelligence/app/schemas/contractor.py`
   - eksik `ContractorParcelContactsResponse` eklendi

3. Frontend correctness fix yapildi:
   - `england_map_web/internet_access_overlay.js`
   - Internet layer artik varsayilan olarak `sales-history` proxy fallback kullanmiyor

4. Uygulama acilabiliyor:
   - `http://127.0.0.1:8010/england_map_web/`

5. Ama Internet layer henuz tamam degil:
   - endpoint cevap veriyor
   - fakat parcel thematic output bos veya renderable geometry yok

## Ana problem

Elimizdeki resmi Ofcom paketi parcel-level degil, postcode-level:

- `F:\chatgpt\AAYS_WORK\internet_access_score10_real_build_20260610\processed\parcel_internet_access_scores.geojson`
- feature var ama `geometry: null`
- yani bu dosya haritada parcel polygon thematic layer olarak cizilemez

Manifest kaniti:

- `status=PROCESSED_PACKAGE_READY_POSTCODE_LEVEL_OFFICIAL_SOURCE`
- `geometry_policy=null geometry only; no fake coordinates`
- `db_write=false`
- `production_deploy=false`

## ChatGPT gorevi

Senin gorevin "tamamlandi" demek degil. Senin gorevin eksik parcayi kapatacak metinleri ve patch planlarini uretmek:

1. Eksiklerin kesin listesini ver
2. Parcel-level Internet layer icin gercek pipeline tasarimini yaz
3. Gerekli yeni dosyalari veya patchleri tek tek ver
4. D/F drive odakli local calisma planini yaz
5. Final kabul kriterini tekrar kur

## Yasaklar

- Fake geometry uretme
- Fake parcel_id uretme
- "null geometry de yeterli" deme
- Sales History katmanini Internet fallback olarak onermeye geri donme
- FINAL_READY veya %100 urun tamamlandi deme
- Baska page key veya baska branch onerme

## Senden istenen cikti

Asagidaki basliklarla cevap ver:

1. `Gercek Eksikler`
2. `Parcel-Level Cozum Tasarimi`
3. `Guncellenecek / Eklenecek Dosyalar`
4. `ChatGPT'nin Yazacagi Patch Metinleri`
5. `Operatorun Localde Calistiracagi PowerShell Adimlari`
6. `D/F Drive Klasor Yapisi`
7. `Kabul Testleri`
8. `Tamamlandi Demek Icin Zorunlu Kosullar`

## Hangi dosyalara odaklan

Mevcut frontend/backend:
- `england_map_web/internet_access_overlay.js`
- `england_map_web/app.js`
- `terrayield_land_intelligence/app/api/routes/map_layers.py`

Muhtemel yeni local output / script yollar:
- `F:\chatgpt\AAYS_WORK\internet_access_parcel_final_20260623\scripts\build_parcel_internet_dataset.py`
- `F:\chatgpt\AAYS_WORK\internet_access_parcel_final_20260623\scripts\import_parcel_internet_dataset.ps1`
- `F:\chatgpt\AAYS_WORK\internet_access_parcel_final_20260623\processed\parcel_internet_access_scores.geojson`
- `F:\chatgpt\AAYS_WORK\internet_access_parcel_final_20260623\processed\parcel_internet_access_scores.csv`
- `F:\chatgpt\AAYS_WORK\internet_access_parcel_final_20260623\processed\parcel_internet_access_factor_breakdown.csv`
- `F:\chatgpt\AAYS_WORK\internet_access_parcel_final_20260623\manifests\parcel_internet_access_manifest.json`

## Kritik ayrim

Asagidaki iki seyi karistirma:

- report chain final
- urunun gercek parcel thematic layer olarak calismasi

Bu is sadece su durumda tamam sayilir:

1. Internet iconu acilir
2. Parcel polygonlar renkli gorunur
3. Tiklanan parcel popup veya sag panelde zorunlu alanlar gorunur
4. Factor table gorunur
5. Kaynak, tarih, confidence ve calculation explanation gorunur
6. DB veya fallback artifact gercek parcel geometry ile beslenir

Bu kosullar saglanmadan %100 deme.
