# Distance to Nearby Property Types - ChatGPT Handoff Paketi

Bu paket, `Distance to Nearby Property Types` katmaninin gercek durumunu dusuk Codex kullanimi ile ChatGPT tarafina devretmek icin hazirlandi.

## Duz ve dogru durum

- Kod entegrasyonu var.
- Frontend baglantisi var.
- Backend route var.
- Popup ve sag panel contract'i var.
- Canli parcel polygon sonucu bu makinede hala bloklu.
- Su an dogru ilerleme seviyesi: yaklasik `%75`.
- `100%`, `FINAL_READY` veya `production complete` denemez.

## Neden tam degil

Ana blokajlar:

1. Local PostGIS / DB runtime ayakta degil.
2. `http://127.0.0.1:8010/map/distance-property-types?...` endpoint'i `200` donuyor ama `features=[]`.
3. `http://127.0.0.1:8010/health` cevabinda `database=degraded`.
4. Shared runner / bridge zinciri bu page-key icin aktif degil, stale durumda.
5. Elimizdeki `parcel_use6_lookup.json` veri seti siniflama verisi tasiyor ama dogrudan gercek parcel geometri kaynagi degil.

## Bu paketin amaci

Bu paket tam uygulama fix'i yapmaz. Sunlari saglar:

- Eksiklerin tek tek matrisi
- ChatGPT'ye verilecek master prompt
- Exact path listesi
- D/F disk odakli PowerShell runbook
- Local probe scriptleri
- ChatGPT'nin yapabilecegi / yapamayacagi islerin ayrimi

## Onerilen agir calisma kokleri

Agir isleri C yerine burada yap:

- `F:\chatgpt\AAYS_WORK\distance_property_types_page34_20260623`
- `D:\AAYS_DATA\distance_property_types_page34_20260623`
- `F:\chatgpt\handoffs\distance_property_types_page34_20260623`

## Paket icerigi

- `01_CHATGPT_MASTER_PROMPT_TR.md`
- `02_GAP_MATRIX_TR.md`
- `03_PATHS_AND_LOCATIONS_TR.md`
- `04_POWERSHELL_RUNBOOK_TR.md`
- `05_EVIDENCE_SUMMARY_TR.md`
- `scripts\10_prepare_df_roots.ps1`
- `scripts\20_distance_property_types_runtime_probe.ps1`
- `scripts\30_export_handoff_zip_to_f.ps1`

## Hemen sonraki adim

1. `scripts\10_prepare_df_roots.ps1` calistir.
2. `scripts\20_distance_property_types_runtime_probe.ps1` calistir.
3. Urettigi raporu ve bu klasoru ChatGPT'ye ver.
4. `01_CHATGPT_MASTER_PROMPT_TR.md` metnini ChatGPT'ye yapistir.

## Stop rule

Asagidaki dordunun hepsi gercekten saglanmadan bu katman tamamlandi denmez:

1. `/health` icinde DB degraded olmamali
2. `/map/distance-property-types?...` endpoint'i bos olmayan `features` donmeli
3. Haritada parcel polygon'lar gorunmeli
4. Parcel tiklaninca popup / sag panel zorunlu alanlari gostermeli
