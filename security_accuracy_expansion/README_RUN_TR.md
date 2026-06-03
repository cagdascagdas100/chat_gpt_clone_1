# Security Accuracy Expansion

Bu klasor, AAYS/TerraYield icindeki mevcut `Guvenlik` ve `Dusuk Review` modullerine dokunmadan guvenlik-dogruluk genisletme calismasi icin izole plan, sema, kanit ve QA altyapisini tutar.

## Audit Ozeti

- Canli yukleyici: `C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\index.html`
- Canli guvenlik katmani: `C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\security_overlay.js`
- Canli dusuk-review katmani: `C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\remaining_low_review_overlay.js`
- Canli guvenlik verisi: `C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\data\parcel_security_scores_rechecked_0_120m_spatial.geojson`
- Canli dusuk-review verisi: `C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\data\remaining_low_current_review.geojson`
- Guvenlik feature sayisi: `92,283`
- Dusuk-review feature sayisi: `242`
- Mevcut `downgrade_violations`: `0`

Hash ve audit kayitlari:

- `C:\Users\cagda\Documents\GitHub\AAYS\security_accuracy_expansion\audit\live_surface_hashes_20260507.csv`
- `C:\Users\cagda\Documents\GitHub\AAYS\security_accuracy_expansion\audit\preflight_audit_20260507.md`

## Klasor Yapisi

- `source_catalog/`: resmi/kamu kaynak kataloglari
- `evidence_templates/`: kanit ve run-manifest sablonlari
- `schemas/`: evidence schema
- `qa/`: kabul kriterleri ve checklist
- `methodology/`: upstream plan ve methodology notlari
- `prompts/`: ChatGPT ve Codex handoff promptlari
- `codex_tasks/`: gorev taslaklari
- `frontend/`: entegrasyon taslagi
- `audit/`: bu repodaki canli yuzey snapshot'i

## Low-Credit Calisma Modeli

1. Bu klasordeki audit dosyalarini baz al.
2. ChatGPT'ye sadece bu klasoru ve canli dosya hash CSV'sini ver.
3. ChatGPT'den sadece `security_accuracy_expansion` altinda yeni kanit/manifests/reports uretmesini iste.
4. Canli overlay veya canli geojson degisiklikleri icin her zaman once `verify_live_modules_unchanged.ps1` calistir.
5. PASS almadan `england_map_web` altinda hicbir dosya degistirme.

## ChatGPT'ye Verilecek Dosyalar

- `C:\Users\cagda\Documents\GitHub\AAYS\security_accuracy_expansion\README_RUN_TR.md`
- `C:\Users\cagda\Documents\GitHub\AAYS\security_accuracy_expansion\audit\preflight_audit_20260507.md`
- `C:\Users\cagda\Documents\GitHub\AAYS\security_accuracy_expansion\audit\live_surface_hashes_20260507.csv`
- `C:\Users\cagda\Documents\GitHub\AAYS\security_accuracy_expansion\methodology\01_security_accuracy_expansion_plan.md`
- `C:\Users\cagda\Documents\GitHub\AAYS\security_accuracy_expansion\methodology\03_methodology_and_confidence_model.md`
- `C:\Users\cagda\Documents\GitHub\AAYS\security_accuracy_expansion\methodology\07_risk_limits_and_language.md`
- `C:\Users\cagda\Documents\GitHub\AAYS\security_accuracy_expansion\source_catalog\official_security_source_catalog.json`
- `C:\Users\cagda\Documents\GitHub\AAYS\security_accuracy_expansion\source_catalog\source_evidence_matrix.csv`
- `C:\Users\cagda\Documents\GitHub\AAYS\security_accuracy_expansion\evidence_templates\source_evidence_template.json`
- `C:\Users\cagda\Documents\GitHub\AAYS\security_accuracy_expansion\evidence_templates\run_manifest_template.json`
- `C:\Users\cagda\Documents\GitHub\AAYS\security_accuracy_expansion\evidence_templates\parcel_security_evidence_template.json`
- `C:\Users\cagda\Documents\GitHub\AAYS\security_accuracy_expansion\schemas\parcel_security_evidence_schema.json`
- `C:\Users\cagda\Documents\GitHub\AAYS\security_accuracy_expansion\qa\acceptance_criteria.md`
- `C:\Users\cagda\Documents\GitHub\AAYS\security_accuracy_expansion\prompts\CHATGPT_LOCAL_EXECUTION_PROMPT_TR.md`

## Oncesi ve Sonrasi Kontrol

Oncesi:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "C:\Users\cagda\Documents\GitHub\AAYS\security_accuracy_expansion\audit\verify_live_modules_unchanged.ps1"
```

Sonrasi:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "C:\Users\cagda\Documents\GitHub\AAYS\security_accuracy_expansion\audit\verify_live_modules_unchanged.ps1"
```

Rollback:

- `C:\Users\cagda\Documents\GitHub\AAYS\security_accuracy_expansion\rollback\ROLLBACK_TR.md`
