# future_growth_3 — Wave 38

- Tarih: 2026-07-22
- Kaynaklar: Blackpool Borough Council, Milton Keynes City Council, Peterborough City Council, City of Bradford Metropolitan District Council
- Araştırılan / uygun: 32 / 32
- Yüksek kaynak güveni: 32
- Ortalama kaynak güveni: 98,19 / 100
- Görünür web satırları: 32 aday + 48 işlem

## QA

- 32 benzersiz authoritative entity ve 32 resmî POINT doğrulandı.
- 29 satırda structured kapasite; 3 satırda yalnız described kapasite korundu.
- Milton Keynes provider alan değerleri dönüştürülmeden ve semantik inceleme etiketiyle korundu.
- Peterborough kayıtları authoritative historical entity olarak tutuldu; güncel provider endpoint durumu açıkça işaretlendi.
- Bradford'daki dört resmî sıfır structured kapasite değeri değiştirilmedi; anlatı kapasitesi ayrı alanda tutuldu.
- Bath and North East Somerset kayıtları yetersiz resmî POINT kapsamı nedeniyle geocoding yapılmadan seçilmedi.
- Sahte veri, canonical parsel ataması ve future-growth skoru: 0.

## Canonical blocker

10 yeni repository sorgusu ile toplam arama sayısı 161'e çıkarıldı. Canonical 61.523–92.283 shard export, stable parcel identifier, row-count receipt ve CRS manifesti bulunamadı. Bu nedenle crosswalk ve 30.761 satırlık skor matrisi başlatılmadı.

`final_ready=false`, `db_write=false`, `migration=false`, `production_deploy=false`.
