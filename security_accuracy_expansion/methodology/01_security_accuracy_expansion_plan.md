# Kaynak Dışı Genişletme Planı

## Aşama 0 — Audit
Mevcut uygulama, data dosyaları ve güvenlik overlay dosyaları kontrol edilir. Aktif dosyalar değiştirilmez.

## Aşama 1 — Kaynak kataloglarını kur
`official_security_source_catalog.json` ve `source_evidence_matrix.csv` proje içine alınır.

## Aşama 2 — Kanıt dosyaları üret
Her kaynak için aşağıdaki kanıtlar şablona göre doldurulur:
- kaynak URL'si
- erişim zamanı
- dosya boyutu
- checksum
- satır/feature sayısı
- kapsama alanı
- tarih aralığı
- lisans/koşul notu
- alan/kolon şeması

## Aşama 3 — İngiltere geneli veri genişletme
Öncelik sırası:
1. data.police.uk bulk downloads
2. data.police.uk API sample validation
3. ONS LSOA boundaries
4. ONS Postcode Directory
5. OS Open UPRN
6. HM Land Registry INSPIRE polygons
7. IoD 2025 Crime Domain
8. Yerel AAYS parsel geometrileri

## Aşama 4 — Spatial matching pipeline
- Parcel polygon/point → LSOA point-in-polygon
- Parcel centroid → nearest LSOA boundary distance
- UPRN → LSOA lookup fallback
- Postcode → LSOA lookup fallback
- INSPIRE polygon → parcel/title geometry fallback

## Aşama 5 — Cross-source scoring
Safety skoru ayrı, confidence ayrı hesaplanır. Confidence sadece kanıt seviyesi yeterliyse yükselir.

## Aşama 6 — Evidence-backed frontend
Haritada her parsel popup'ında sadece sonuç değil, kanıt özeti de gösterilir:
- source_count
- source_reliability_score
- parcel_match_score
- confidence_flags
- last_updated
- evidence_manifest_id

## Aşama 7 — QA ve rollback
Her run sonunda QA manifest yazılır. Mevcut çalışan güvenlik modülü bozulursa rollback uygulanır.
