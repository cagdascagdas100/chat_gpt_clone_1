# future_growth_2 — Object-ID Replay and Pagination Bundle — Batch 019 — 2026-07-23

## Sonuç
- Batch işlemleri: **900/900 PASS**
- Kümülatif işlemler: **4,742 → 5,642**
- Resmî kaynaklar: **129 → 134**
- Ağ şablonları: **270** (`240` statik + `30` dinamik object-ID replay)
- Adaylar: **3** (`30762`, `46142`, `61522`)
- Exact parcel binding: **0**
- Business rows: **0**
- Çıktı: `future_growth_score=null`, `confidence_pct=0`, `data_status=NO_DATA`

## Doğruluk yükseltmesi
ArcGIS feature yanıtlarının kayıt sınırına güvenilmez. Her seçilmiş katmanda `returnIdsOnly` ile ID listesi alınır ve aynı sıralı ID kümesi ikinci bir resmî `objectIds` sorgusunda tekrar istenir. `exceededTransferLimit=true`, eksik/tekrarlı ID, iki CRS kimlik farkı veya kayıt sayısı farkı bağlamayı engeller.

## Kaynak yönetişimi
Yeni beş resmî sayfa Feature Layer metadata, Feature Service query, development-plan-document-type, development-plan-type ve site-category kaynaklarıdır. Boş ya da MHCLG referans verisi parsel kanıtına çevrilmez.

## Engel
Kanonik tek runner görevi başka slotta `pickup_requested` durumundadır. Canlı 270 şablon sonucu ve hash zinciri repoya yazılmadığı için manual action açık kalır. Büyük 92,283 satırlık blob doğrudan indirmesi DNS nedeniyle başarısız olduğundan ek örnek satır uydurulmamıştır.
