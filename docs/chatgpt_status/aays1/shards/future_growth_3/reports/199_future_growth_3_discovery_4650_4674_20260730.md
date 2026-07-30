# future_growth_3 — discovery wave 4650–4674

- Tarih: 2026-07-30 17:24 +03:00
- Continuation key: `61383520c6a16ecbb0bd2f3d65f26f06ed73185e4b2d7845f096dbcd3a985d91`
- Kapsam: Manchester, Bristol, Leicester ve Sheffield resmî brownfield kayıtları
- İşlenen: 25 yeni entity
- Strict eligible: 18
- Fail-closed: 7
- Ortalama eligible güveni: 99/100
- Repo mükerrerlik araması: 25/25 temiz
- Resmî kaynak kanalı: 11
- Canonical export araması: 395 sorgu / 0 eşleşme
- Canonical satır eşleşmesi: 0
- Business satırı: 0

## Yüksek sinyal

- Manchester `CC_Cap_002a`: 1.746
- Manchester `CC_Cap_804`: 800
- Manchester `CC_Cap_709`: 200–500
- Manchester `Chor_Cap_030`: 190–350
- Manchester `Dean1904`: 231
- Bristol `17/04673/F`: 120
- Leicester `LPM0921`: 73

## Fail-closed

- `Anco_Cap_711`: minimum 880, maksimum 600; ters kapasite aralığı.
- `18/06722/F`: yapılandırılmış minimum kapasite eksik. Web istemcisi iki kez 503 verdi; sonsuz tekrar yapılmadı ve değer çıkarılmadı.
- `S02057`: yalnız not metninde konut sayısı; yapılandırılmış min/max yok.
- `S02599`: end-date 2020-01-22 ve minimum kapasite eksik.
- `S01226`: end-date 2020-01-22 ve yalnız not metni kapasitesi.
- `S02607`: end-date 2022-08-01 ve minimum kapasite eksik.
- `S03700`: student-cluster notu net dwelling kapasitesi olarak yorumlanmadı.

## Güvenlik ve semantik

- POINT değerleri canonical parsel poligonu değildir.
- Canonical export olmadan parsel ataması, yakınlık eşlemesi veya future-growth skoru üretilmedi.
- PDF içeriğinden alan çıkarımı yapılmadı.
- Kullanıcı eylemi gerekmiyor; `NO_DATA_CONTINUE` altında resmî kaynak araştırması sürdürülebilir.

## Kanıt yolları

- `england_map_web/data/aays_21_slots/future_growth_3/wave_4650_4674_20260730.json`
- `england_map_web/data/aays_21_slots/future_growth_3/wave_4650_4674_20260730.html`
- `england_map_web/data/aays_21_slots/future_growth_3/index.html`

`final_ready=false`, `fake_data=false`, `db_write=false`, `production_deploy=false`.
