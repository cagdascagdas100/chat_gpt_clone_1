# Internet Access ChatGPT Handoff 20260616

Bu paket, TerraYield AAYS icindeki `Internet` katmanini dusuk Codex kredisiyle ChatGPT + yerel PowerShell uzerinden tamamlatmak icin hazirlandi.

Bu paketin rolu:

- ChatGPT'ye verilecek ana promptu saglamak
- mevcut eksikleri kesin kanitla listelemek
- ChatGPT'nin yapabilecegi isleri Codex/local shell islerinden ayirmak
- agir veri islerini `F:` veya `D:` surucusune yonlendirmek
- kullaniciya tekrar Codex'e donmeden once yerelde neyi nasil kontrol edecegini gostermek

Bu paketteki en onemli dosyalar:

- `00_CHATGPT_MASTER_PROMPT_TR.md`
- `01_GAP_STATUS_TR.md`
- `02_CHATGPT_VS_LOCAL_SPLIT_TR.md`
- `03_LOCAL_POWERSHELL_RUNBOOK_TR.md`
- `04_PATHS_AND_OUTPUTS_TR.md`
- `05_MACHINE_READABLE_TASKS.json`
- `06_AFTER_CHATGPT_RETURN_CHECKLIST_TR.md`
- `07_UPLOAD_LIST_TR.md`

Referans klasoru:

- `references\README_TR.md`
- `references\CURRENT_STATE_AUDIT_TR.md`
- `references\04_INTERNET_ACCESS_OUTPUT_CONTRACT_TR.md`
- `references\06_ACCEPTANCE_TESTS_TR.md`
- `references\codex-open-smoke-20260616-1518.md`

Yerel shell yardimcilar:

- `scripts\10_prepare_heavy_root.ps1`
- `scripts\20_validate_current_package.ps1`
