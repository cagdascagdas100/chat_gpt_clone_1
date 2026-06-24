CODEX / CHATGPT TRANSFER PROMPT - TerraYield AAYS / Gas Emissions / Low Credit Completion

Bu promptu ChatGPT'ye aynen ver. Scope'u dar tut ve sadece `Gas Emissions` katmanina odaklan.

Sabit kapsam

- Repo: `cagdascagdas100/chat_gpt_clone_1`
- Branch: `feature/terrayield-aays-integration`
- Katman: `Gas Emissions`
- Lokal C repo sadece referans olabilir:
  `C:\Users\cagda\Documents\GitHub\AAYS`
- Asil calisma kokunu C disinda tut:
  tercih `F:\chatgpt\AAYS_WORK\gas_emissions_088_clean_20260616_160836`
- F kok yoksa fallback:
  `D:\chatgpt\gas_emissions_runtime_finish_20260622`
- `D:\AAYS` koku varsayma. Yoksa fail-closed davran.

Kati kurallar

1. Baska branch varsayma.
2. Baska layer veya genel refactor yapma.
3. Fake data uretme.
4. DB write, migration, deploy yapma.
5. Buyuk GeoJSON'u yeni blob olarak GitHub'a pushlamaya zorlama.
6. Sadece ikon/legend calisiyor diye `FINAL_READY` deme.
7. Kabul kuralini su sekilde uygula:
   - layer acilacak
   - sadece veri olan parcel/polygon thematic gorunumu olacak
   - parcel tiklaninca popup veya sag panelde zorunlu alanlar dolu olacak
   - source/evidence/confidence/explanation gorunecek

Bu zip icindeki dosyalar source of truth

1. `02_GAS_EMISSIONS_GAP_REPORT_TR.md`
2. `03_DF_WORKTREE_RUNBOOK_TR.md`
3. `04_POWERSHELL_COMMANDS_TR.md`
4. `05_ACCEPTANCE_CHECKLIST_TR.md`
5. `07_GAS_EMISSIONS_SCHEMA_SAMPLE.json`
6. `08_MATCH_EVIDENCE_SAMPLE.json`
7. `england_map_web_app.js`
8. `england_map_web_index.html`
9. `codex-gas-emissions-audit-20260622-215101.md`
10. `codex-gas-emissions-integration-smoke-20260616-2330.txt`
11. `codex-gas-emissions-runtime-smoke-20260622-182759.md`

Once bunlari oku, sonra cevap ver.

Halihazirda dogrulanmis gercekler

1. `http://127.0.0.1:8010/england_map_web/` aciliyor.
2. `england_map_web/data/parcel_emissions_scores.geojson` aktif checkout icinde mevcut.
3. `air.png` icon binding var.
4. `node --check england_map_web/app.js` geciyor.
5. Layer runtime'da aciliyor ve legend `4246` feature gosteriyor.
6. Ama runtime hala `geometryMode=point_source`.

Asil eksik problem

`Gas Emissions` su anda gercek parcel polygon thematic layer olarak kapanmis degil. Kodda polygon join yolu var, ama aktif calisan mod direct point-source. Bunu teknik olarak kapatacak plan lazim.

ChatGPT'den beklenen cikti

1. Ilk bolum: `VERIFIED NOW`
   - zip ve dosyalardan kesin dogrulananlar
2. Ikinci bolum: `MISSING FOR TRUE COMPLETION`
   - tek tek eksik maddeler
3. Ucuncu bolum: `ROOT CAUSES`
   - hangi dosya/satir/mantik eksikligi engelliyor
4. Dorduncu bolum: `PATCH PLAN`
   - sadece gerekli minimal patch plani
   - buyuk refactor yapma
5. Besinci bolum: `CHATGPT-WRITABLE OUTPUTS`
   - bana `apply_patch` bloklari ver
   - gerekiyorsa sadece `england_map_web/app.js` ve `england_map_web/index.html` icin
6. Altinci bolum: `LOCAL POWERSHELL STEPS`
   - F veya D kokunde kullanilacak komutlar
7. Yedinci bolum: `PASTE-BACK OUTPUTS`
   - benim sana geri gondermem gereken minimum terminal/browser ciktilari
8. Sekizinci bolum: `STOP RULE`
   - su kosullar saglanmadan `FINAL_READY` deme

Ozellikle incele

1. `directSourceMode`
2. `buildVisiblePolygonFeatures()`
3. `getLookupMatch()`
4. `ensureDatasetLoaded()`
5. `findGasEmissionsRecordForParcel()`
6. `buildGasEmissionsPopupMetaHtml()`
7. `buildParcelPopupContent()`
8. `openParcelPopup()` ve `refreshActiveParcelPopup()`

Asagidaki sorulari cevapla

1. `polygon_join` neden devreye girmiyor?
2. `buildVisiblePolygonFeatures()` neden yeterli parcel polygon dondurmuyor?
3. `point_source` fallback korunurken parcel polygon thematic mod nasil eklenir?
4. Popup/sag panelde gas alanlari hangi tek kaynaktan beslenmeli?
5. Sag panel entegrasyonu eksikse minimum ek blok nereye konmali?
6. Performans dusmeden nasil fail-soft yapilir?

Teslim formati

Su basliklarla cevap ver:

- VERIFIED NOW
- MISSING FOR TRUE COMPLETION
- ROOT CAUSES
- PATCH PLAN
- APPLY_PATCH BLOCKS
- LOCAL POWERSHELL STEPS
- PASTE-BACK OUTPUTS
- STOP RULE

Ek not

Lutfen sadece teorik yorum yapma. Kopyalanabilir patch ve komut ver. Ama local browser smoke'u kendin yaptigini varsayma; browser sonucu icin benden paste-back iste.
