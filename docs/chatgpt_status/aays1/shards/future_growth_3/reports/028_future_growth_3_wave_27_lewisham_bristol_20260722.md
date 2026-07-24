# future_growth_3 — Wave 27 Lewisham ve Bristol resmî kaynak genişletmesi

Tarih: 2026-07-22  
Slot: `future_growth_3`  
Shard: 61,523–92,283 (30,761 satır)

## Sonuç

- London Borough of Lewisham resmî standardize Brownfield Land tablosundan 10 satır araştırıldı.
- Bristol City Council resmî standardize Brownfield Land tablosundan 6 satır araştırıldı.
- 16/16 satır source-candidate olarak uygun ve authoritative point kaydıdır.
- Dalga kaynak güveni 98.5/100.
- Global brownfield reference değerlerinin farklı idarelerde çakışabildiği doğrulandı; bu nedenle `authority + reference` bileşik anahtarı kullanıldı.
- Yalnız bağımsız olarak doğrulanan Convoys Wharf kaydında entity `1705026` tutuldu; diğer 15 satır için entity ID tahmin edilmedi.
- Point geometri canonical parsel poligonu olarak yükseltilmedi.
- Canonical parsel ID ve Future Growth skoru üretilmedi.

## Kümülatif

- Araştırılan: 493
- Uygun: 449
- Dışlanan: 44
- Yüksek kaynak güvenli: 481
- Ortalama uygun kaynak güveni: 98.24/100
- Resmî kaynak ailesi: 84
- Web görünürlüğü: 16 aday satırı ve 24 işlem satırı
- Canonical ürün satırı: 0/30,761
- Operasyonel ilerleme: 7/12 (%58.33), 1 kısmi

## Blocker

`CANONICAL_SHARD_61523_92283_EXPORT_NOT_FOUND_IN_REMOTE_REPOSITORY`

`final_ready=false`, `fake_data=false`, `db_write=false`, `migration=false`, `production_deploy=false`.