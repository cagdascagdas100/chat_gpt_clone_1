# AAYS 8.1 Gercek 100 Kapanis - Bagimlilik ve Paralel Calisma Plani

Tarih: 2026-05-24
Sayfa: 8.1 Gelisim

## Neden yeni plan gerekli?
Onceki hizli kapanis `project_100_finalize` sadece status finalizasyonuydu. Codex entegrasyonu sonrasi gercek eksikler goruldu:

1. DEM raster dosyalari local ortamda bulunamadi.
2. `git pull` islemleri local `ai-tasks/current-task.json` degisikligi yuzunden cakisti.
3. `current-task`, `.last-task-id` ve heartbeat bazi turlarda senkron degildi.
4. `real100v2evidence1` sonucu `overall_progress=94` ve `review_queue_ready_external_approval_required` durumunu verdi.
5. Gercek 100 icin bagimli dogrulamalar ayrilmali: DEM, API, DB preflight, queue-lock, paket/result kanitlari.

## Ana ilke
Sahte 100 yok. `overall_progress=100` sadece kritik kapilarin tamamlanmasi veya non-blocking uyari sinifina alinmasi halinde yazilir.

## Bagimli / bagimsiz isler

### Paralel calisabilecek bagimsiz isler
Ayni tek runner script'i icinde PowerShell background job olarak paralel kosar:

A. DEM job
- `E:\AAYS_DATA\elevation\copernicus_dem_glo30` kontrol edilir.
- Eksik iki Copernicus DEM dosyasi gercek S3 kaynagindan yeniden indirilmeye calisilir.
- Dosya boyutu ve varlik kontrolu yapilir.
- Fake raster uretilmez.

B. API/asset smoke job
- `http://127.0.0.1:8010/england_map_web/`
- `http://127.0.0.1:8010/api/future-growth/layer?zoom=10&limit=1`
- `http://127.0.0.1:8010/api/future-growth/parcels/1`
- Future Growth ikon asset path kontrolu.

C. Contractor DB preflight evidence job
- `C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-results\terrayield-079-contractor-db-env-loader-preflight.audit.json` okunur.
- `connection_ok=true`, `db_query_ok=true` aranir.
- DB write yapilmaz.

D. Queue/local git hygiene job
- `git status --short` okunur.
- `ai-tasks/current-task.json` local degisikligi varsa rapora yazilir.
- Destructive `git reset` yapilmaz.

E. Result/evidence inventory job
- Project finalize, DEM result, contractor010-013, c15/r16, integration report varligi kontrol edilir.

### Bagimli isler
1. DEM job sonucunda en az iki DEM dosyasi mevcutsa AAYS112/topography rerun icin hazirlik kapisi acilir.
2. API smoke gecerse Future Growth UI/API kapisi acilir.
3. Contractor preflight gecerse DB erisim kapisi read-only olarak acilir.
4. Tum kritik kapilar gecerse `real_100_parallel_closure` status `finished_real_100_ready` olur.
5. Kritik kapilardan biri kalirsa `finished_with_blockers` olur, 100 yazilmaz.

## Guvenlik
- DB write=false
- production_deploy=false
- fake_data=false
- tek runner korunur
- queue-lock korunur
- current-task dogrudan ezilmez; gorev pending queue'ya alinir

## Cikti dosyalari
- `ai-results/aays_8_1_real100_parallel_closure_20260524.result.json`
- `ai-results/aays_8_1_real100_parallel_closure_20260524.report.md`
- `docs/integration/AAYS_8_1_REAL_100_CLOSURE_STATUS_20260524.md`

## Kullanici akisi
Kullanici sadece `devam et` yazar. Runner gorevi almazsa ancak o zaman PowerShell komutu verilir.
