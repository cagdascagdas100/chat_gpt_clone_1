# future_growth_3 — resmî kaynak doğrulama dalgası 4529–4536

- Zaman: 2026-07-30T14:14:00+03:00
- Continuation key: `61383520c6a16ecbb0bd2f3d65f26f06ed73185e4b2d7845f096dbcd3a985d91`
- İncelenen mevcut uygun aday: **8**
- Yükseltilen kaynak kaydı: **8**
- Referans verilen ayrı resmî kanal: **10**
- Resmî site-plan bağlantısı bulunan satır: **7**
- Güvenli tekrar ile kurtarılan doğrudan okuma: **1** (`PR111`)
- Ortalama satır güveni: **99/100**
- Yeni aday: **0**
- Canonical parsel eşleşmesi / business satırı: **0**

## Satırlar

1. Dudley `151`: 20 konut, güncel authoritative kayıt ve resmî Dudley planlama haritası bağlantısı.
2. Wolverhampton `D97d`: 99 konut, Wolverhampton Brownfield Register/SHLAA kanalı ve resmî ArcGIS site-plan bağlantısı.
3. Solihull `PR97`: 1 konut, permissioned 2021-11-10, Solihull register ve resmî PR97 site-plan bağlantısı.
4. Solihull `PR86`: 2 konut, permissioned 2020-11-09, Solihull register ve resmî PR86 site-plan bağlantısı.
5. Solihull `PR90`: 1 konut, full planning permission 2021-02-12, Solihull register ve resmî PR90 site-plan bağlantısı.
6. Solihull `PR100`: 3 konut, permissioned 2021-04-01, Solihull register ve resmî PR100 site-plan bağlantısı.
7. Solihull `PR111`: 1 konut, permissioned 2022-05-24; ilk doğrudan okuma hatası tek güvenli tekrar ve resmî indeks sonucu ile kurtarıldı.
8. Wolverhampton `D83`: 2 konut, Wolverhampton register/SHLAA ve resmî ArcGIS site-plan kanalı.

## Doğruluk disiplini

- Yalnız güncel Planning Data authoritative entity kayıtları ve resmî yerel yönetim kanalları kullanıldı.
- Site-plan PDF içeriklerinden alan çıkarımı yapılmadı; yalnız resmî bağlantıların varlığı ve current entity satırındaki alanlar kaydedildi.
- POINT değerleri canonical parsel poligonu olarak yorumlanmadı.
- Canonical shard 61.523–92.283 exportu bulunmadığı için parsel kesişimi ve future-growth skoru üretilmedi.
- `final_ready=false`, `fake_data=false`, `NO_DATA_CONTINUE`.
