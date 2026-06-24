Gas Emissions / ChatGPT Handoff / 2026-06-22

Amac

Bu paket, `Gas Emissions` katmaninin eksik kalan kisimlarini Codex kredisi harcamadan daha cok ChatGPT + lokal PowerShell uzerinden kapatmak icin hazirlandi.

Bu pakette ne var

1. `01_CHATGPT_MASTER_PROMPT_TR.md`
2. `02_GAS_EMISSIONS_GAP_REPORT_TR.md`
3. `03_DF_WORKTREE_RUNBOOK_TR.md`
4. `04_POWERSHELL_COMMANDS_TR.md`
5. `05_ACCEPTANCE_CHECKLIST_TR.md`
6. `06_CHATGPT_CAN_CANNOT_DO_TR.md`
7. `07_GAS_EMISSIONS_SCHEMA_SAMPLE.json`
8. `08_MATCH_EVIDENCE_SAMPLE.json`
9. Kopya kanit dosyalari:
   - `england_map_web_app.js`
   - `england_map_web_index.html`
   - `codex-gas-emissions-audit-20260622-215101.md`
   - `codex-gas-emissions-integration-smoke-20260616-2330.txt`
   - `codex-gas-emissions-runtime-smoke-20260622-182759.md`

Onemli durum

1. ChatGPT rapor zinciri `FINAL_READY/100` demis olsa da aktif runtime kabul kriterini tam kapatmiyor.
2. Katman aciliyor, `air.png` ikonu calisiyor, legend geliyor, `4246` feature gorunuyor.
3. Ama runtime hala `geometryMode=point_source`. Bu, orijinal parcel-based thematic layer kabul kuralini saglamiyor.
4. Popup/parcel detail tarafinda da tam kapanmis runtime kaniti yok.

Tercih edilen lokal kok

1. Tercih edilen F worktree:
   `F:\chatgpt\AAYS_WORK\gas_emissions_088_clean_20260616_160836`
2. Fallback D koku:
   `D:\chatgpt\gas_emissions_runtime_finish_20260622`

Not

Bu paketi tek parca olarak ChatGPT'ye verebilirsin. Ilk adim olarak `01_CHATGPT_MASTER_PROMPT_TR.md` icerigini kullan.
