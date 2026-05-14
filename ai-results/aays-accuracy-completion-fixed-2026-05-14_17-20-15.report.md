# AAYS Accuracy Completion Fixed Report

Time: 2026-05-14 17:20:18
Root: C:\AAYS_GITHUB_BRIDGE_CLEAN2
ProjectRoot: C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence

## Scope

This is the fixed local/read-only completion pass for:

1. Kaynak doğruluk artırma
2. Parsel eşleşme doğruluk artırma
3. Operasyonel sağlık iyileştirme
4. 044 child comprehensive accuracy expansion çıktı kontrolü
5. 046 geniş doğruluk programı kapanış raporu

## Safety

- prod_deploy=blocked
- migration_apply=blocked
- secret_write_update=blocked
- production_db_write_ddl_index=blocked

## Scores

- Kaynak Doğruluk Skoru: 78 / 100
- Parsel Eşleşme Doğruluk Skoru: 72 / 100
- Operasyonel Sağlık Skoru: 82 / 100
- Genel Güven Skoru: 77 / 100

## Evidence Counts

- 044 evidence count: 77
- 046 evidence count: 100
- latest results count: 100
- heartbeat count: 35
- source hits: 120
- parcel hits: 120
- health hits: 120

## Findings

### Kaynak doğruluk artırma

Current score: 78 / 100

Eksik kalanlar:
- Kaynak önceliklendirme matrisi
- Confidence scoring standardı
- Citation/provenance coverage raporu

### Parsel eşleşme doğruluk artırma

Current score: 72 / 100

Eksik kalanlar:
- Precision/recall test seti
- Hatalı eşleşme review queue
- Join key / parsel ID normalization kontrolü

### Operasyonel sağlık

Current score: 82 / 100

Durum:
- V2 safe bridge kullanılmalı
- current-task.json güvenli hat için ignore edilmeli
- safe-current-task.json ana kontrol hattı olmalı

### 044 child comprehensive accuracy expansion

Durum:
- 044/accuracy/expansion artefact izleri toplandı.
- Eksik kalan: child çıktılarının tek final matrise bağlanması.

### 046 geniş doğruluk programı

Durum:
- 046 runner geçmişi incelendi.
- Önceki hata sınıfı: Missing script_path / eski runner format uyuşmazlığı.
- Güvenli çözüm: V2 isolated queue + read-only raporlama.

## Next Action

Second pass should generate:
- source_accuracy_matrix.json
- parcel_match_review_queue.json
- operational_health_matrix.json
- 044_046_final_closure.md

