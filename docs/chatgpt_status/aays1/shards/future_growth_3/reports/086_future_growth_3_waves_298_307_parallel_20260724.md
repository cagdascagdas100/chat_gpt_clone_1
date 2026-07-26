# future_growth_3 — waves 298–307 — 2026-07-24

## Sonuç
- Aynı continuation key ile devam edildi; ikinci runner oluşturulmadı.
- 10 otorite grubu, 55 tekil resmî brownfield adayı araştırıldı.
- Direct-live: 74 aday çağrısı = 40 PASS / 34 FAIL; 17 tek güvenli retry; 38 unique PASS / 17 unique FAIL.
- Ek alan doğrulaması: 6 secondary field-readback çağrısı.
- Strict ≥98 kapısı: 25 uygun, 30 dışlama; uygun ortalama güven 98.44/100.
- 25/25 uygun satırda exact POINT ve pozitif structured minimum-net-dwellings var.
- Search-only promotion = 0.
- Görünür kanıt: 55 aday satırı + 385 işlem satırı.

## Öne çıkan uygun adaylar
- Derbyshire Dales SHLAA266: minimum 1100.
- Derbyshire Dales SHLAA500: 367.
- Derbyshire Dales SHLAA269: 151.
- Bradford NW/002: 129.
- Barnsley TCDS2: 88; HS14: 82; HS49: 65.
- Bradford CU/001: 53.
- South Derbyshire LP Policy H3: minimum 44.
- North East Derbyshire NW/1702: 41.

## Fail-closed örnekleri
- Bradford CR/014: direct authoritative kayıt mevcut ancak structured minimum-net-dwellings = 0; dışlandı.
- North East Derbyshire WW/1610 (2): structured toplam 489 iken notlarda 183 konutun tamamlandığı yazıyor; residual kapasite ile structured alan uyumsuz olduğu için dışlandı.
- Calderdale BLR201: structured minimum eksik; dışlandı.
- High Peak HD012: lapsed permission semantiği; dışlandı.
- 17 aday direct entity sayfasında ilk ve tek retry sonrası da cache miss verdi; search snapshot ile promote edilmedi.

## Kümülatif durum
- Araştırılan: 2796
- Uygun: 1662
- Dışlanan: 1134
- Yüksek güven: 1574
- Ortalama uygun kaynak güveni: 98.20/100
- Resmî kaynak ailesi: 112
- Uygun kaynak konumu: 1662/1662
- Ana operasyon: 7 tamam + 1 kısmi / 12 = 58.33%
- Canonical eşleşme: 0/30761

## Blocker
`CANONICAL_SHARD_61523_92283_EXPORT_NOT_FOUND_IN_REMOTE_REPOSITORY`

Canonical export, stable parcel ID/row-count/CRS kanıtı olmadan POINT verisi canonical parsel ataması olarak kullanılmadı. Kullanıcı eylemi gerekmiyor. final_ready=false; fake_data=false; db_write=false; migration=false; production_deploy=false.
