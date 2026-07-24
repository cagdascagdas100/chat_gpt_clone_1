# future_growth_3 — Wave 30 Lambeth Planning Data API

- Tarih: 22.07.2026
- Slot: `future_growth_3`
- Shard: `61523-92283`
- Resmî kaynak ailesi: London Borough of Lambeth / MHCLG Planning Data API
- Yeni aday: 32
- Uygun / authoritative: 32 / 32
- Ortalama kaynak güveni: 98.69 / 100
- Görünür web satırı: 32 aday + 48 işlem
- Canonical parsel eşleşmesi / skor / iş satırı: 0 / 0 / 0

## Örnekler

- Central Hill Estate — 503 konut
- Somerleyton Road / Coldharbour Lane — 304 konut
- 44 Clapham Common South Side — 293 konut
- 12-20 Wyvil Road — 278 konut
- South Lambeth Estate — 261 konut
- Tesco, 263-275 Kennington Lane — 248 konut
- Pope's Road Car Park — 240 konut, açık end-date
- Fenwick Estate — 236 konut

## QA

- 32 benzersiz entity ve authority+reference anahtarı.
- 31 tarih-sonlu kayıt `freshness-review` olarak korundu.
- 10 anlatı/structured kapasite farkında structured dwelling alanı değiştirilmedi.
- BLR023 temporal tutarsızlığı düzeltilmiş gibi gösterilmedi.
- Nokta geometrileri canonical parsel poligonu olarak yükseltilmedi.
- Sahte veri, DB yazımı, migration ve production deploy yok.

## Canonical blocker

Bu turda 5 yeni repository/commit sorgusu çalıştırıldı; eşleşme bulunmadı. Exact 30.761 satırlık canonical shard export, stabil parsel kimliği ve CRS bildirimi bulunmadan crosswalk veya skor üretilmedi.

`final_ready=false`
