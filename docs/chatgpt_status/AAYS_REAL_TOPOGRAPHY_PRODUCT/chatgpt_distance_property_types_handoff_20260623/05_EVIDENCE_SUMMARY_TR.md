# Evidence Summary - Distance to Nearby Property Types

## 1) Integration report ozeti

Kaynak:

- `docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/reports/codex_distance_property_types_integration_20260617_02.md`

Temel sonuc:

- status: `PARTIAL_PRODUCT_READY_DB_BLOCKED`
- frontend baglandi
- backend route eklendi
- popup ve sag panel contract'i eklendi
- ama local runtime `database=degraded`
- bu nedenle endpoint bos `FeatureCollection` donuyor

## 2) Runtime wrapper probe ozeti

Kaynak:

- `docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/reports/page34_runtime_wrapper_probe_20260623_153149.md`

Temel sonuc:

- `progress_estimate=75`
- `final_ready_confirmed=False`
- `bridge_current_task_page_key=security_public_safety_low_credit_20260612`
- bu page-key ile eslesmiyor
- bridge heartbeat stale
- runner polling likely false

Blokaj satirlari:

- `runtime_wrapper_missing_or_final_markers_absent`
- `shared_runner_not_polling_or_not_pushing_outputs`
- `bridge_current_task_page_key_mismatch`
- `bridge_runner_heartbeat_stale`

## 3) Canli endpoint gercegi

Bugune kadar dogrulanan gercek:

- `GET /health` -> `200`
- health cevabinda DB degraded
- `GET /map/distance-property-types?...` -> `200`
- ama `features=[]`

Bu ne anlama gelir:

- uygulama URL'i acilabilir
- route vardir
- ama gercek parcel layer veri akisi tamam degildir

## 4) Veri kaynagi siniri

Mevcut lookup:

- `terrayield_land_intelligence/data/exports/parcel_use6/parcel_use6_lookup.json`

Bu dosya siniflama alanlari tasir:

- `parcel_id`
- `use6_code`
- `use6_label_tr`
- `use6_color_hex`
- `dogruluk_skalasi`
- `confidence`
- `kaynak_ve_belirleme_yontemi`

Ama bu dosya tek basina gercek parcel polygon geometry kaynagi degildir.

## 5) Dogru sonuc

Bu layer icin simdiki dogru cumle:

> Kod entegrasyonu yapildi, ama gercek parcel polygon runtime kabulunu saglayan DB/runtime zinciri henuz ayakta degil.
