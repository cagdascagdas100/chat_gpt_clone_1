# Güvenilirlik Artırma Metodolojisi

## Amaç
Mevcut güvenlik modülünün güvenilirlik seviyesini artırmak için tek kaynaklı skor yerine çok kaynaklı, kanıt dosyalı ve parsel bazlı izlenebilir bir model kurmak.

## Temel ilke
- Resmî/kamu kaynakları önceliklidir.
- Her kaynağın indirme tarihi, şema, satır sayısı, dosya hash'i ve kapsama alanı kanıtlanır.
- Kanıt yetersizse kayıt otomatik yükseltilmez.
- Confidence skoru ile safety skoru ayrı tutulur.
- “Kesin güvenlik” yerine “kanıta dayalı güvenilirlik seviyesi” kullanılır.

## Kaynak güvenilirlik skoru
Her kaynak için 0–100 arası `source_reliability_score` hesaplanır.

Önerilen ağırlıklar:
- Resmî kaynak statüsü: %25
- Veri tazeliği: %20
- Mekânsal çözünürlük: %20
- Kapsama/completeness: %20
- Şema/kanıt bütünlüğü: %15

## Parsel eşleşme skoru
Her parsel için 0–100 arası `parcel_match_score` hesaplanır.

Önerilen ağırlıklar:
- Direkt parcel polygon / centroid LSOA eşleşmesi: %35
- UPRN veya postcode destekli konum köprüsü: %20
- ONS LSOA polygon içinde kalma: %20
- Kaynaklar arası uyum: %15
- Eksik veri/flag cezası: %10

## Confidence 4 seviye
- 75–100: Cok Yuksek
- 55–74: Yuksek
- 35–54: Orta
- 0–34: Dusuk

## Güvenlik 5 seviye
- 0–20: Cok Dusuk
- 20–40: Dusuk
- 40–60: Orta
- 60–80: Iyi
- 80–100: Cok Iyi

## Cross-source agreement
Bir parsel/LSOA için şu kaynaklar aynı yönde sinyal verirse confidence yükselir:
- data.police.uk son 12/24 ay suç yoğunluğu
- IoD 2025 Crime Domain relatif risk sıralaması
- MPS/London LSOA verisi varsa bölgesel uyum
- ONS/OS/HMLR spatial matching kalitesi

## Flag sistemi
- LOW_RECENCY: kaynak tarihi eski
- LOW_SPATIAL_MATCH: parsel geometri eşleşmesi zayıf
- LOW_COVERAGE: kaynak kapsaması eksik
- SOURCE_MISMATCH: kaynaklar ters yönde sinyal veriyor
- NO_UPRN_LINK: UPRN bağlantısı yok
- NO_POSTCODE_LINK: postcode bağlantısı yok
- OUTSIDE_LSOA_POLYGON: nokta/polygon LSOA içinde değil
- REVIEW_REQUIRED: otomatik yükseltme yapılmamalı

## Kabul kriteri
- Her kaynak için evidence JSON var.
- Her işleme run manifest var.
- Her parsel için source_count, confidence_label, confidence_flags alanları var.
- Low confidence kayıtlar review katmanında duruyor.
- No-downgrade ihlali yok.
