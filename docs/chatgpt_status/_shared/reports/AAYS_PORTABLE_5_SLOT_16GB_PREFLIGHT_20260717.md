# AAYS Portable 5 Slot / 16 GB Preflight - 2026-07-17

## Sonuc

- Portable root, scriptin bulundugu klasorden cozulur; drive letter kalici kimlik degildir.
- Portable Python ve portable Git F disk icindedir.
- Tek coordinator en fazla 5 slot worker kullanir; ikinci coordinator lock ile engellenir.
- Bes light-read fixture ayni anda calisti.
- RAM, raster, geometry, browser acceptance, Git publish ve shared publish agir isleri serialize edilir.
- Yanlis slot, duplicate task ve shared path overlap fixture testlerinde engellendi.
- Sabit URL http://127.0.0.1:8012; health, ana uygulama ve OpenAPI HTTP 200 verdi.

## Donanim Profilleri

- Mevcut PC: 7.31 GB RAM, 12 logical CPU, low_memory_8gb.
- Yeni nesil i5 + 16 GB: balanced_16gb; 5 hafif/network slot eszamanli, agir isler kontrollu sirali.
- 16 GB sistem uygundur. Ayni anda 5 agir browser/raster/geometry isi calistirilmaz.

## Yeni PC Akisi

1. Portable diskin kokundeki AAYS_PORTABLE_CONTROL_PANEL.cmd acilir.
2. Yeni PC On Kontrol calistirilir.
3. Uygulama + 5 Slot Baslat secilir.
4. Bes ChatGPT sayfasinin her biri yalniz kendi slotunda devam et ile remote checkpointten ilerler.

## Gercek Testler

- Python syntax: PASS
- PowerShell parse: PASS
- portable preflight: PASS
- portable Git: git version 2.51.0.windows.1
- fixture concurrency: 5/5
- resource heavy peaks: 1
- alternate drive simulation: PASS
- second launch blocked: PASS
- coordinator working set idle: 17.5 MB
- HTTP 8012 health/main/openapi: 200/200/200
- physical second-PC test: NOT_RUN (ikinci PC bu oturumda bagli degil)

final_ready=false; business data completion iddiasi yoktur.