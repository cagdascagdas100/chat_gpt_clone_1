# future_growth_3 — waves 2022–2081 — 2026-07-27

## Sonuç
- Araştırılan: 60
- Strict uygun: 23
- Fail-closed: 37
- Ortalama uygun kaynak güveni: 98,98/100
- Promoted duplicate: 0/23
- Search-only promotion: 0
- Yeni resmî kaynak/otorite ailesi: +4

## Uygun otoriteler
- City of York Council
- Middlesbrough Borough Council
- Hartlepool Borough Council
- Northumberland County Council

## Kalite kapıları
- Exact authoritative entity readback zorunlu.
- End-date boş/current.
- Minimum ve maximum net dwellings pozitif.
- Resmî POINT zorunlu.
- Repo duplicate kontrolü 23/23.
- Cache miss için en fazla bir güvenli retry.
- POINT canonical parsel poligonu değildir.

## QA dağılımı
- 13 temporal/end-dated
- 3 structured-capacity eksik veya non-positive
- 3 tek güvenli retry sonrası fail
- 6 direct readback tamamlanamadı, fail-closed
- 12 discovery-only, exact direct readback olmadan terfi edilmedi

## Direct protokol
- 46 unique direct candidate
- 49 direct çağrı
- 37 unique PASS
- 9 unique FAIL
- 3 safe retry
- üçüncü retry: 0

## Kümülatif
- 5.650 araştırılan
- 2.658 uygun
- 2.992 dışlanan
- 2.570 yüksek güven
- ortalama uygun güven 98,33
- 216 resmî kaynak/otorite ailesi
- uygun kaynak konumu 2.658/2.658 = %100
- canonical row match 0
- ürün satırı 0/30.761

## Canonical export
- Yeni bounded sorgu: +3
- Kümülatif: 269 / 0 indexed match
- State: NO_DATA_CONTINUE
- Manual action gerektirmez.

## Güvenlik
- Canonical parsel eşleştirmesi yapılmadı.
- Future-growth skoru üretilmedi.
- DB/migration/deploy yok.
- fake_data=false
- final_ready=false
