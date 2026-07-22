# future_growth_3 — Wave 48 Bristol resmî kaynak raporu

- Tarih: 2026-07-22
- Continuation key: `61383520c6a16ecbb0bd2f3d65f26f06ed73185e4b2d7845f096dbcd3a985d91`
- Hedef canonical aralık: 61.523–92.283 (30.761 satır)
- Durum: Kaynak araştırması tamamlandı; canonical export manuel engeli açık.

## Sonuç

- Araştırılan: 30
- Uygun: 30
- Dışlanan: 0
- Yüksek güven (>=95): 30
- Ortalama güven: 97,60/100
- Exact resmî POINT: 30/30
- Yapılandırılmış kapasite: 29
- Açıklama-temelli kapasite: 1
- Resmî kaynak readback: 30 PASS / 0 FAIL
- Görünür aday satırı: 30
- Görünür işlem satırı: 153
- Kaynak kanalı yükseltmesi: 1 — resmî Bristol provider tablosu ikinci canlı otoritatif kanal olarak kabul edildi.
- Yeni kaynak ailesi: 0; çapraz-dalga tam registry kanıtı olmadığı için kümülatif sayı 112 tutuldu.

## Doğrulama yöntemi

29 kayıt MHCLG Planning Data entity sayfalarından, bir kayıt Bristol City Council resmî provider tablosundan doğrulandı. POINT, kapasite, hektar, izin durumu/türü/tarihi ve kayıt tarihleri doğrudan resmî alanlardan alındı. Eksik alanlar null bırakıldı. Pending kararlar permissioned olarak yükseltilmedi. Aynı konumdaki farklı izin referansları farklı kayıtlar olarak korundu.

## QA bulguları

- 4 pending-decision kaydı ve eksik izin tarihi
- 3 durum/tarih çelişkisi
- 1 tarihsel end-date kaydı
- 1 açıklama-temelli kapasite kaydı
- 1 kapasite aralığı
- 2 aynı konumda farklı izin referansı
- Eski veya çok eski izin tarihleri açık bayraklarla korundu

## Canonical engel

İki yeni exact repo aramasında da rows 61.523–92.283 için 30.761 satırlık canonical export, stable parcel identifier, row-count/range receipt veya CRS manifest bulunmadı. Kümülatif canonical arama sayısı 183, eşleşme 0. Bu nedenle:

- canonical parsel eşleştirmesi yapılmadı,
- POINT kayıtları parsel poligonu sayılmadı,
- future-growth skoru üretilmedi,
- ürün satırı yazılmadı.

`fake_data=false`, `final_ready=false`, `db_write=false`, `migration=false`, `production_deploy=false`.
