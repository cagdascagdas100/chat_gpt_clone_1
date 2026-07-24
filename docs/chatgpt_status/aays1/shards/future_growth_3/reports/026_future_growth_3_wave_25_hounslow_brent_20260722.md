# future_growth_3 — Wave 25 Hounslow ve Brent resmî kaynak örnekleri

Tarih: 2026-07-22 03:49 Europe/Istanbul  
Slot: `future_growth_3`  
Shard: 61,523–92,283 (30,761 satır)

## Bu dalgada yapılanlar

- London Borough of Hounslow ve London Borough of Brent resmî kaynak aileleri araştırıldı.
- MHCLG Planning Data authoritative entity kayıtlarından 16 source-candidate işlendi.
- 16/16 satır uygun ve yüksek kaynak güvenli bulundu.
- Dalga ortalama kaynak güveni: `99.25/100`.
- Her satırda resmî kaynak referansı, entity bağlantısı, point geometri, saha adı, idare, kapasite ve planlama durumu kaydedildi.
- Hounslow satırlarındaki dört boş entry-date alanı uydurulmadı ve açık inceleme etiketiyle bırakıldı.
- Point geometriler canonical parsel poligonu olarak yükseltilmedi.

## Görünür web kanıtı

- `england_map_web/data/aays_21_slots/future_growth_3/wave_25_20260722.html`
- `england_map_web/data/aays_21_slots/future_growth_3/operations_wave_25_20260722.html`
- `england_map_web/data/aays_21_slots/future_growth_3/index.html`

Web panelinde 16 aday satırı; aday kimliği, kaynak referansı, saha, idare, giriş tarihi, kapasite, planlama durumu, kaynak güveni, geometri durumu, canonical parsel ve skor sütunlarıyla gösterilir. Canonical parsel ve skor değerleri kanıt bulunmadığı için `NULL` kalır.

## Kalite sonucu

- Araştırılan: `16`
- Uygun: `16`
- Dışlanan: `0`
- Authoritative kaynak: `16`
- Resmî point geometri: `16`
- HTTPS kaynak: `16`
- Dalga ortalama kaynak güveni: `99.25/100`
- Canonical eşleşme: `0`
- Future Growth skoru: `0`
- Yazılan gerçek ürün satırı: `0`

## Kümülatif durum

- Araştırılan: `465`
- Uygun source-candidate: `421`
- Dışlanan: `44`
- Yüksek kaynak güvenli: `453`
- Ortalama uygun kaynak güveni: `98.24/100`
- Resmî kaynak ailesi: `80`
- Canonical ürün satırı: `0/30,761`
- Operasyonel ilerleme: `7/12`, bir kısmi operasyon (`58.33%`)

## Blocker

`CANONICAL_SHARD_61523_92283_EXPORT_NOT_FOUND_IN_REMOTE_REPOSITORY`

Exact 30,761-row canonical export, stable parcel ID, polygon geometry, range receipt ve CRS manifesti olmadan candidate-to-parcel crosswalk veya Future Growth skoru üretilmedi.

`final_ready=false`, `fake_data=false`, `db_write=false`, `migration=false`, `production_deploy=false`.