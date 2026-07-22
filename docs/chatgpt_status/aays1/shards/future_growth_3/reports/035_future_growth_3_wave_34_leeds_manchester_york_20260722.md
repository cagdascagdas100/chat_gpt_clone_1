# future_growth_3 — Wave 34

## Sonuç
- Resmî kaynak aileleri: Leeds City Council, Manchester City Council, City of York Council.
- Araştırılan / uygun / yüksek güvenli: 36 / 36 / 36.
- Ortalama kaynak güveni: 99.03 / 100.
- Web görünürlüğü: 36 aday satırı ve 54 işlem satırı.
- Exact resmî entity ve EPSG:4326 nokta: 36 / 36.

## QA
- 7 tarih-sonlu kayıt ve 4 legacy tarih incelemesi açıkça işaretlendi.
- 6 structured/not kapasite farkında structured değer değiştirilmedi; açıklama ayrı tutuldu.
- 10 provider kapasite semantiği satırı yeniden yorumlanmadı.
- Manchester Anco_Cap_712 için güncel entity görünümü ile eski CURIE görünümü arasındaki kapasite/tarih farkı `source_fact_conflict` olarak kaydedildi; güncel entity alanları korundu.
- Eksik minimum, izin tarihi, entry tarihi veya plan durumu tahmin edilmedi.
- Canonical parsel ve skor alanları 36/36 satırda NULL kaldı.
- Sahte veri: 0.

## Canonical export araması
- Toplam indeksli repo sorgusu: 121.
- Bu dalgada yeni sorgu: 8; eşleşme: 0.
- İncelenen slot commitine bağlı PR-triggered workflow run: 0.
- Bilinen artifact ID: yok.

## Kümülatif
- Araştırılan: 689.
- Uygun: 645.
- Dışlanan: 44.
- Yüksek kaynak güveni: 677.
- Uygun kaynak güveni ortalaması: 98.44 / 100.
- Resmî kaynak ailesi: 100.
- Uygun kaynak konumu: 645 / 645.
- Canonical eşleşme ve skor: 0 / 30,761.

## Blocker
`CANONICAL_SHARD_61523_92283_EXPORT_NOT_FOUND_IN_REMOTE_REPOSITORY` devam ediyor. Canonical kimlik, geometri/CRS manifesti ve 30,761 satırlık doğrulama makbuzu olmadan point-to-parcel ataması veya skor üretimi yapılmadı.

`final_ready=false`, `fake_data=false`, `db_write=false`, `migration=false`, `production_deploy=false`.
