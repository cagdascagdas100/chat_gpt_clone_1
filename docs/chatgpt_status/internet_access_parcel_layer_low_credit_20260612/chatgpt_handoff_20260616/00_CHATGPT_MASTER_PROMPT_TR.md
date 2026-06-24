# CODEX TRANSFER PROMPT - Internet Access Final Parcel Layer Recovery

Bu promptu aynen uygula.

## Scope

Sadece TerraYield AAYS icindeki `Internet` katmani.

## Repo / Page

- Repo: `cagdascagdas100/chat_gpt_clone_1`
- Branch: `feature/terrayield-aays-integration`
- Page key: `internet_access_parcel_layer_low_credit_20260612`
- Local repo root: `C:\Users\cagda\Documents\GitHub\AAYS`

## Disk Kurali

Agir veri, processed paket, rapor, diagnostics, Excel ve gecici build ciktilarini `C:` yerine `F:` veya `D:` surucusune yaz.

Oncelikli agir calisma root'u:

- `F:\AAYS_WORK\internet_access_final_20260616\`

F yoksa alternatif:

- `D:\AAYS_WORK\internet_access_final_20260616\`

Repo icindeki kucuk patch/dokuman dosyalari haric buyuk veri uretimini `C:` altina yazma.

## Source Of Truth

Bu ZIP icindeki asagidaki dosyalari ana kaynak kabul et:

- `01_GAP_STATUS_TR.md`
- `04_PATHS_AND_OUTPUTS_TR.md`
- `05_MACHINE_READABLE_TASKS.json`
- `references\CURRENT_STATE_AUDIT_TR.md`
- `references\04_INTERNET_ACCESS_OUTPUT_CONTRACT_TR.md`
- `references\06_ACCEPTANCE_TESTS_TR.md`
- `references\codex-open-smoke-20260616-1518.md`

## Mevcut Dogrulanmis Durum

1. Frontend toggle / runtime bridge / backend route mevcut:
   - `england_map_web/app.js`
   - `england_map_web/internet_access_overlay.js`
   - `terrayield_land_intelligence/app/api/routes/map_layers.py`

2. Report chain mevcut ve final-ready isaretli:
   - `ia106.json`
   - `internet-access-105-shared-runner-package-and-validate.json`
   - `internet-access-107-final-ready-gate.json`

3. Harici veri paketi mevcut:
   - `F:\chatgpt\AAYS_WORK\internet_access_score10_real_build_20260610\processed\parcel_internet_access_scores.csv`
   - `F:\chatgpt\AAYS_WORK\internet_access_score10_real_build_20260610\processed\parcel_internet_access_scores.geojson`
   - `F:\chatgpt\AAYS_WORK\internet_access_score10_real_build_20260610\processed\parcel_internet_access_factor_breakdown.csv`
   - `F:\chatgpt\AAYS_WORK\internet_access_score10_real_build_20260610\reports\internet_access_parcel_report.xlsx`

4. Ama bu paket final parcel layer degil:
   - GeoJSON `50000` feature iceriyor ama tum feature geometry degeri `null`
   - `calculation_manifest.json` icinde:
     - `status=PROCESSED_PACKAGE_READY_POSTCODE_LEVEL_OFFICIAL_SOURCE`
     - `geometry_policy=null geometry only; no fake coordinates`
     - `db_write=false`
     - `production_deploy=false`

Bu nedenle ozellik `report-chain tamam` olsa da `parcel-level thematic layer tamam` degildir.

## Senin Gorevin

Asagidaki kalan isleri tam ve ayri ayri tamamla:

### A. Eksikleri Tek Tek Kapat

1. Postcode-level / null-geometry paketi parcel-renderable ciktiya donustur
2. Gercek parcel polygon veya renderable geometry olmadan "tamam" deme
3. Faktor breakdown contract'ini gercekten tamamla
4. Sag panel / popup icin kullanilacak veri yapisini netlestir
5. `F:` veya `D:` altinda final artifact setini uret
6. Repo'ya uygulanacak patch metinlerini ayri dosyalar halinde ver

### B. Final Output Package Uret

Asagidaki ciktilari agir root altinda uret:

- `processed\parcel_internet_access_scores_ready.csv`
- `processed\parcel_internet_access_scores_ready.geojson`
- `processed\parcel_internet_access_factor_breakdown_ready.csv`
- `processed\parcel_internet_access_detail_ready.json`
- `reports\internet_access_parcel_report_ready.xlsx`
- `reports\internet_access_gap_closeout.md`
- `diagnostics\internet_access_blockers.json`
- `repo_patch\PATCH_APP_JS.diff`
- `repo_patch\PATCH_INTERNET_OVERLAY.diff`
- `repo_patch\PATCH_MAP_LAYERS.diff`
- `repo_patch\PATCH_OPTIONAL_DETAIL_ENDPOINT.diff`

### C. Final Acceptance Kuralini Koruyarak Calis

Asagidaki durumlardan biri varsa ozellik `tamam` sayilmaz:

- parcel polygon yoksa
- GeoJSON geometry hala `null` ise
- sales-history proxy halen primary internet source gibi gorunuyorsa
- faktor table yoksa
- sag panel / popup detay sozlesmesi yoksa
- only icon/toggle calisiyorsa

### D. Tercih Edilecek Tasarim

En guvenli tasarim:

- Ana skor kaynagi:
  - `parcel_internet_access_scores`
- Detay kaynagi:
  - `parcel_internet_access_factors`
  - veya feature bazinda `factor_breakdown` JSON array

### E. ChatGPT'den Beklenen Teslim

1. "Tamamlandi" / "tamamlanmadi" karari
2. Hangi eksigi neyle kapattigin
3. Hangi eksigi kapatamadigin
4. Hangi dosya/path uzerinde ne urettigin
5. Repo icin uygulanabilir patch metni
6. Eger blocker varsa net JSON/MD blocker raporu

## Upload Gercegi

Eger sana sadece bu ZIP veriliyor ama `F:` veya `D:` altindaki buyuk veri dosyalari upload edilmiyorsa:

- buyuk veri dosyalarini sanki gormussun gibi davranma
- "tamamlandi" deme
- bunun yerine local PowerShell/Python donusum scripti, patch metni ve exact runbook uret
- verinin bizzat islenmesi icin kullanicinin yerelde calistiracagi komutlari ver

Yani tam veri seti yoksa `artifact processing script + repo patch` modu ile calis.

## Yapmaman Gerekenler

- fake geometry uretme
- `production_complete=true` deme
- null geometry paketi parcel layer gibi sunma
- proxy mode'u production kabul etme
- agir artifact'lari `C:` altina yazma

## Codex'e Geri Donus Formati

Donuste su basliklarla cevap ver:

1. `Completion percent`
2. `Closed gaps`
3. `Open gaps`
4. `Generated files on F/D`
5. `Repo patch targets`
6. `Can Codex integrate now? yes/no`

