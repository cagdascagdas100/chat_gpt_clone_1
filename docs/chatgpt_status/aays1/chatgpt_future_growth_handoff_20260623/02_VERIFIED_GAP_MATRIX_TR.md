# Verified Gap Matrix

| Alan | Durum | Dogrulama | Sahip |
| --- | --- | --- | --- |
| Final wrapper raporu | Eksik | `docs/chatgpt_status/aays1/reports/aays1_sync_unblock_then_future_growth_wrapper_20260619_008.txt` yok | Local runtime |
| `main` / aays1 urun koku | Uyusmuyor | izole `main` worktree icinde `app.js` security shell gostermekte | Local repo / Codex |
| Methodology endpoint | Var | `http://127.0.0.1:8010/api/future-growth/methodology` cevap verdi | Verified now |
| Layer endpoint | Timeout | `http://127.0.0.1:8010/api/future-growth/layer?...` bounded probe timeout | Local runtime |
| Docker | Calismiyor | `docker ps` pipe baglantisi yok | Local runtime |
| Shared runner script path | Eksik | handoff'un referans verdigi `_shared/automation/RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER.ps1` `main` icinde yok | Local repo |
| Frontend FG layer wiring | Var | `england_map_web/app.js` icinde source/layer/toggle/legend/popup kodu mevcut | Verified now |
| Backend FG route wiring | Var | `terrayield_land_intelligence/app/api/routes/future_growth.py` mevcut | Verified now |
| Detail API contract | Kismen eksik | schema/detail response icinde `probability_status`, `calculation_explanation`, `no_data_reason` yok | ChatGPT patch |
| Popup binding | Kismen eksik | popup `growth_probability_percent`, `probability_status`, `calculation_explanation`, version/horizon disclaimer gostermiyor | ChatGPT patch |
| Popup disclaimer | Eksik | zorunlu disclaimer string'i mevcut degil | ChatGPT patch |
| Right-side panel binding | Dogrulanmadi | popup var; sag panel icin net binding bu auditte kanitlanmadi | Local + ChatGPT |

## Somut kod eksikleri

### Backend schema eksikleri

Kaynak: `terrayield_land_intelligence/app/schemas/future_growth.py`

`FutureGrowthParcelDetailResponse` icinde su alanlar yok:

- `probability_status`
- `layer_name`
- `calculation_explanation`
- `no_data_reason`

### Backend service eksikleri

Kaynak: `terrayield_land_intelligence/app/future_growth/evidence_service.py`

`get_parcel_detail()` su alanlari donmuyor:

- `probability_status`
- `layer_name`
- `calculation_explanation`
- `no_data_reason`

### Frontend popup eksikleri

Kaynak: `england_map_web/app.js`

`buildFutureGrowthParcelPopupContent()` su alanlari gostermiyor:

- `growth_probability_percent`
- `probability_status`
- `calculation_version`
- `horizon_years`
- `calculated_at`
- `calculation_explanation`
- zorunlu `not guaranteed price prediction` disclaimer

## ChatGPT'nin yapamayacagi kisimlar

- Docker daemon acmak
- 8010 runtime layer timeout'u lokal ortamda kesinlemek
- shared runner'in gercekten task tuketip tuketmedigini calistirarak dogrulamak
- final wrapper'i gercek runtime olmadan dogru saymak
