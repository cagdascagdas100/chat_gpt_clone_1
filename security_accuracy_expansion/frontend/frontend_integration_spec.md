# Frontend Entegrasyon Taslağı

## Amaç
Topografik/harita sayfası açıldığında güvenlik modülü katman olarak hazır olmalı; ancak veri işleme frontend içinde değil, önceden hazırlanmış GeoJSON/tiles üzerinden yapılmalı.

## Yeni UI fikirleri
- Guvenlik butonu mevcut kalsın.
- Dusuk Review butonu mevcut kalsın.
- Yeni panel: `Kaynak Kanıtı`
  - Data.police güncellik
  - LSOA eşleşme durumu
  - UPRN/Postcode/INSPIRE kanıtı
  - Source agreement
  - Confidence flags

## Popup alanları
- safety_score / safety_level
- confidence_score / confidence_label
- source_count
- source_reliability_score
- parcel_match_score
- evidence_manifest_id
- confidence_flags
- review_action

## Performans önerisi
92k+ feature için GeoJSON çalışıyor; tüm İngiltere kapsamı büyürse PMTiles/vector tile veya zoom-level lazy loading kullanılmalı.
