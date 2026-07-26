# future_growth_3 — waves 1842–1901 — 2026-07-26

## Sonuç
- Araştırılan resmî brownfield satırı: 60
- Strict uygun: 43
- Fail-closed: 17
- Uygun kaynak güveni: 98.79/100
- Search-only promotion: 0
- Promoted repo duplicate: 0/43
- Yeni kaynak aileleri: East Suffolk Council, Norwich City Council, Cambridge City Council, Swindon Borough Council

## Strict gate
Terfi için exact authoritative Planning Data entity sayfası, boş/current end-date, pozitif structured minimum+maximum net dwellings, resmî POINT ve repo duplicate=0 birlikte zorunludur.

## Kalite dağılımı
- Temporal/end-dated: 8
- Structured capacity non-positive: 1
- Tek güvenli retry sonrası direct readback fail: 8
- Third retry: 0
- Tracked direct calls: 62
- Tracked unique direct PASS: 46
- Tracked unique direct FAIL: 8

## Servis recovery
Planning Data erişiminde geçici 503/DNS sorunu gözlendi. Sorun sırasında promotion yapılmadı; servis toparlandıktan sonra exact entity readback ile devam edildi. Açık PENDING bırakılmadı.

## Örnek yüksek kapasite adaylar
- C/LocalPlan/R47 | 18/0481/OUT — 780
- N/THH/008 — 300
- ES018 — 250–300
- N/THH/021 — 242
- 17/2245/FUL | 18/1947/S73 | 19/0175/FUL — 236
- N/MAN/003 — 200
- 06/0552/FUL — 156
- N/MAN/018 — 151

## Kümülatif
- Araştırılan: 5,470
- Uygun: 2,578
- Dışlanan: 2,892
- Yüksek güven: 2,490
- Ortalama uygun kaynak güveni: 98.30/100
- Kaynak aileleri: 200
- Uygun kaynak konumu: 2,578/2,578 = 100%
- Canonical export audit: 260 sorgu / 0 eşleşme
- Canonical ürün satırı: 0/30,761
- Ana operasyon: 7/12 + 1 kısmi = 58.33%

## Güvenlik
POINT canonical parcel polygon değildir. Canonical export/crosswalk olmadan parcel assignment, future-growth score veya business/product row yazılmadı. `final_ready=false`.
