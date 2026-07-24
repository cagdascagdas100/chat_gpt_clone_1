# future_growth_3 — Wave 37 (Dartford + Plymouth)

## Sonuç
- Araştırılan: 28
- Uygun authoritative aday: 16
- Kaynak-geometri eksikliği nedeniyle dışlanan negatif kontrol: 12
- Ortalama uygun kaynak güveni: 99.06/100
- Yeni resmî kaynak ailesi: 2
- Görünür aday satırı: 16
- Görünür işlem satırı: 36

## Kaynaklar
Dartford Borough Council ve Plymouth City Council kayıtları MHCLG Planning Data üzerindeki exact entity, POINT ve structured kapasite alanlarıyla normalize edildi. Portsmouth City Council için incelenen 12 resmî kayıtta POINT alanı bulunmadığından hiçbir geocoding veya konum tahmini yapılmadı ve kayıtlar aday kümesine yükseltilmedi.

## QA
- 16/16 exact entity ve resmî POINT
- 16/16 structured kapasite
- 8 inceleme etiketli satır
- 1 sıfır minimum değer aynen korundu
- 1 notes/status çatışması ve 1 permission-field semantik incelemesi açık tutuldu
- canonical_row_no, canonical_parcel_id ve future_growth_score: tüm satırlarda NULL
- sahte veri: 0

## Canonical engel
10 yeni repository sorgusunda canonical 61,523–92,283 shard export veya CRS manifesti bulunmadı. Toplam arama sayısı 151, eşleşme 0. Canonical geometri olmadan parsel crosswalk ve skor üretimi başlatılmadı.

final_ready=false; db_write=false; migration=false; production_deploy=false.
