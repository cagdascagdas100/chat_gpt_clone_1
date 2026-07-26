# future_growth_3 — waves 1988–2147 — 2026-07-26

## Sonuç
- 160 gerçek resmî Planning Data araştırma/audit satırı.
- 15 strict uygun, 145 fail-closed.
- Uygun ortalama kaynak güveni: 98.83/100.
- Direct protokol: 29 benzersiz aday, 40 çağrı, 20 unique PASS, 9 unique FAIL after one safe retry, 11 safe retry, üçüncü retry 0.
- Direct-PASS kalite/duplicate dışlaması: 5; search-only promotions: 0.
- Web görünümü: 160 aday satırı + 1,120 QA işlem satırı.

## Yeni strict uygun kayıtlar
- BK090 — Pendle Borough Council — 9 — 99.0
- BLR/IP256 — Ipswich Borough Council — 28 — 98.5
- BLR/IP080 — Ipswich Borough Council — 24–27 — 99.0
- BLR3 — Coventry City Council — 8–24 — 99.0
- 22/05074/FUL — Shropshire Council — 8 — 99.0
- 14/02693/OUT — Shropshire Council — 30 — 98.5
- 20/01284/FUL — Shropshire Council — 3 — 99.0
- 081 — Oxford City Council — 18–59 — 98.5
- 076 — Oxford City Council — 450 — 99.0
- 61 — West Lindsey District Council — 5 — 98.5
- SHB046 — South Tyneside Council — 11 — 98.5
- 18/01027/OUT — Shropshire Council — 58 — 99.0
- SHR016 — Shropshire Council — 9 — 99.0
- 7579 — Cheshire East Council — 5 — 99.0
- BR2 — Cornwall Council — 20–40 — 99.0

## Kümülatif
- 5,716 araştırılan; 2,382 uygun; 3,334 dışlanan/audit; 2,294 yüksek güven.
- Kümülatif uygun güveni: 98.25/100.
- 166 doğrulanmış resmî kaynak ailesi; bu dalgada 9 resmî kanal güçlendirildi/revalidate edildi.
- Uygun resmî kaynak konumu: 2,382/2,382 = 100%.
- Ana pipeline: 7 tamam + 1 kısmi / 12 = 58.33%; operasyonel artış 0.00%.
- Kaynak aday artışı: +15 / +0.63%.
- Canonical ürün: 0/30,761; gerçek business veri yazımı 0.

## Kalite dışlamaları
- BR047: önceki araştırma satırı olduğu için tekrar sayılmadı.
- SHA0021: structured maximum net dwellings eksik.
- P/BLR/0031: 2020 giriş / eski izin temporal kapısı.
- 19/00866/FUL ve 23/00116/FUL: direct entity ile search snapshot arasında source-version/kapasite farkı.
- 9 kayıt bir güvenli retry sonrasında direct readback başarısız olduğu için fail-closed.

## Canonical audit
İki bounded exact repository araması daha yapıldı. Toplam 251 sorgu / 0 eşleşme. Exact 30,761-row canonical shard export, stable parcel ID/geometry, row-count receipt ve CRS manifesti bulunamadı. `NO_DATA_CONTINUE`; kullanıcı eylemi gerekmiyor.

POINT yalnız resmî kaynak konumudur; canonical parsel poligonu değildir. Nearest-parcel inference, future-growth score, DB write, migration veya production deploy yapılmadı.
