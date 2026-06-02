# Preflight Audit 2026-05-07

## Scope

Bu audit, `security_accuracy_expansion` kurulmadan once canli AAYS/TerraYield guvenlik yuzeyini kayda almak icin uretildi.

## Canli Yukleme Noktalari

- `index.html` icinde aktif yuklenen CSS:
  - `./security_overlay.css?v=20260501_021247`
  - `./remaining_low_review_overlay.css?v=20260501_022705`
- `index.html` icinde aktif yuklenen JS:
  - `./security_overlay.js?v=20260501_021247`
  - `./remaining_low_review_overlay.js?v=20260501_022705`

## Canli Veri Baglantilari

- `security_overlay.js` -> `./data/parcel_security_scores_rechecked_0_120m_spatial.geojson`
- `security_overlay.js` -> `./data/parcel_security_match_summary.json`
- `remaining_low_review_overlay.js` -> `./data/remaining_low_current_review.geojson`

## Dogrulanan Canli Sayilar

- `parcel_security_scores_rechecked_0_120m_spatial.geojson` feature count: `92283`
- `remaining_low_current_review.geojson` feature count: `242`
- `parcel_security_match_summary.json.total_parcels`: `92283`
- `parcel_security_match_summary.json.matched_parcels`: `91730`
- `parcel_security_match_summary.json.match_rate`: `0.994`
- `parcel_security_match_summary.json.downgrade_violations`: `0`
- `parcel_security_match_summary.json.confidence_label_counts`: `{'Cok Yuksek': 91730, 'Dusuk': 553}`

## Audit Karari

- PASS: canli guvenlik ve dusuk-review modulleri tespit edildi.
- PASS: canli data dosyalari ve hash baseline kayda alindi.
- PASS: yeni genisletme altyapisi yalnizca `security_accuracy_expansion` altina yerlestirilebilir.
- FAIL kosulu: `england_map_web` altindaki canli overlay dosyalari veya canli geojson dosyalari bu plan asamasinda degisirse.

## Bu Asamadaki Kisit

- Aktif `safety_score` akisi degistirilmeyecek.
- Aktif `confidence_score` akisi degistirilmeyecek.
- Aktif `Guvenlik` ve `Dusuk Review` buton akisi degistirilmeyecek.
- Bu klasor sadece plan, sema, kanit, QA ve audit altyapisidir.
