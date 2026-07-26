# future_growth_3 — waves 1488–1547 — 2026-07-26

## Sonuç

Aynı continuation key ile 60 resmî Planning Data brownfield satırı araştırıldı. 10 kayıt strict source-candidate kapılarından geçti, 50 kayıt fail-closed kaldı. Uygun kayıtların ortalama kaynak güveni 98.90/100.

- researched: 60
- eligible: 10
- excluded/audit: 50
- authority groups: 28
- eligible authorities: 7
- direct candidates: 32
- direct protocol calls: 48
- unique direct PASS: 16
- unique direct FAIL after one safe retry: 16
- direct-PASS quality exclusions: 6
- search-only audit rows: 28
- search-only promotions: 0
- visible candidate rows: 60
- visible QA operation rows: 420

## Strict uygun örnekler

- OSW005 — Shropshire Council — 5–10 dwellings — not-permissioned — 99.0
- BLR73 — Coventry City Council — 25 dwellings — not-permissioned — 99.0
- SHA2147 — Oldham Metropolitan Borough Council — 100 dwellings — not-permissioned — 99.0
- AL6 — Royal Borough of Windsor and Maidenhead — 50 dwellings — not-permissioned — 99.0
- WBR/17/0154 — London Borough of Wandsworth — 191 dwellings — not-permissioned — 98.5
- BR00203 — London Borough of Brent — 40 dwellings — not-permissioned — 99.0
- AL31 — Royal Borough of Windsor and Maidenhead — 47 dwellings — not-permissioned — 99.0
- BLR74 — Coventry City Council — 92–200 dwellings — not-permissioned — 98.5
- AL10 — Royal Borough of Windsor and Maidenhead — 350 dwellings — not-permissioned — 99.0
- UBLR/17/008 — Uttlesford District Council — 9–15 dwellings — not-permissioned — 99.0

## Kalite dışlamaları

Direct readback başarılı olsa bile çelişkili kayıtlar promotion almadı. Örnekler: NSBR0025 notlarında 240 dwellings yazarken structured capacity 95; BFR_0012 notlarda 9 daire iken structured capacity 8; BR00183 arama görünümü ile doğrudan entity entry-date arasında versiyon çatışması; 15/06410/FUL end-dated; BR00175 eski 2020 permission evidence; BFR029 eski permission/status semantik çatışması.

Cache-miss oluşan direct entity sayfalarında yalnız bir güvenli retry yapıldı. İkinci denemede de açılamayan 16 benzersiz kayıt fail-closed tutuldu. Üçüncü retry yapılmadı.

## Kümülatif durum

Önceki checkpoint 1487 üzerine:

- researched: 5,116
- eligible: 2,325
- excluded/audit: 2,791
- high source confidence: 2,237
- average eligible source confidence: 98.25/100
- source families upgraded: 166
- eligible source geometry: 2,325 / 2,325 = 100%
- source-candidate increase: +10 / +0.43%
- main operations: 7 complete + 1 partial / 12 = 58.33%
- canonical product: 0 / 30,761

## Canonical export gate

İki yeni exact repository sorgusu çalıştırıldı ve yeni eşleşme bulunmadı. Audit toplamı 241 sorgu / 0 eşleşme. Canonical 61,523–92,283 export, stable parcel ID/geometry, row-count receipt ve CRS declaration hâlâ yok.

Bu veri yokluğu kullanıcı eylemi değildir. Durum `NO_DATA_CONTINUE`; source research güvenli biçimde devam edebilir. Canonical parcel assignment, nearest-parcel inference, future-growth score, DB write, migration veya production deploy yapılmadı.

## Web görünümü

- `england_map_web/data/aays_21_slots/future_growth_3/wave_1488_1547_20260726.html`
- `england_map_web/data/aays_21_slots/future_growth_3/operations_wave_1488_1547_20260726.html`
- `england_map_web/data/aays_21_slots/future_growth_3/rows_wave_1488_1547_parallel_20260726.json`
- `england_map_web/data/aays_21_slots/future_growth_3/quality_wave_1488_1547_parallel_20260726.json`
- `england_map_web/data/aays_21_slots/future_growth_3/source_url_readback_wave_1488_1547_parallel_20260726.json`

continuation_key: `61383520c6a16ecbb0bd2f3d65f26f06ed73185e4b2d7845f096dbcd3a985d91`

final_ready=false; fake_data=false; db_write=false; migration=false; production_deploy=false.
