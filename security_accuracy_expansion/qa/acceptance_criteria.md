# Kabul Kriterleri

## Plan/şablon aşaması PASS
- Aktif skor/veri dosyaları değiştirilmedi.
- Kaynak kataloğu var.
- Kanıt şablonları var.
- Methodology var.
- QA checklist var.

## Veri indirme aşaması PASS
- Her kaynak için checksum var.
- Her kaynak için row_count/feature_count var.
- Her kaynak için lisans/koşul notu var.
- Hiçbir kaynak “downloaded but unaudited” kalmıyor.

## Skor üretim aşaması PASS
- safety_score 0–100.
- confidence_score 0–100.
- confidence_label 4 seviyeden biri.
- safety_level 5 seviyeden biri.
- source_count var.
- confidence_flags var.
- no-downgrade ihlali yok.

## Frontend aşaması PASS
- Mevcut Guvenlik ve Dusuk Review butonları çalışıyor.
- Yeni kaynak kanıt paneli aktif veriyle çakışmıyor.
- popup içinde evidence_manifest_id gösteriliyor.
