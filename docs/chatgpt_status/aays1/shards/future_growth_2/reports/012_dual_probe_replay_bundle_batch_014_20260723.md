# future_growth_2 — Dual-probe replay bundle / Batch 014

## Sonuç

Batch 014, aynı continuation anahtarı altında 420/420 hazırlık ve doğrulama işlemi üretir. Paket 120 resmî ağ işinden oluşur:

- 30 ArcGIS alt-katman metadata isteği
- 30 ArcGIS count-only nokta-kesişim isteği
- 30 ArcGIS tam özellik nokta-kesişim isteği
- 24 Planning Data koordinat sorgusu
- 6 GLA/Lambeth bölgesel veya birincil sorgu

## Doğruluk yaklaşımı

Her ArcGIS katmanı metadata, count-only ve feature probe ile üç aşamalı ele alınır. Count ve feature kayıt sayıları uyuşmadan bir kesişim bağlanmaz. Her canlı sonuç için tam istek URL'si, URL SHA-256, ham gövde, ham gövde SHA-256, UTC zaman damgası, HTTP durum kodu, içerik türü, JSON ayrıştırma durumu ve API hata durumu zorunludur.

Planning Data koordinat sorgularında sıfır sonuç yalnız sorgulanan dataset için geçerlidir. Planning Data dokümantasyonunda da veri kapsamının bölgeye göre değişebileceği belirtilir. Draft, emerging, scheduled ve adopted plan durumları birbirine dönüştürülmez.

## Resmî kaynak güncellemeleri

- Planning Data API dokümantasyonu: koordinatla geometrik kesişim ve çoklu dataset sorgusu.
- Planning Data brownfield-land: 37.666 kayıt, 354 sağlayıcı, collector 20 Temmuz 2026.
- Planning Data brownfield-site: deneysel, MHCLG üretimi ve authoritative sınırlarla değiştirilmesi bekleniyor.
- GOV.UK plan-verisi standardı: 7 Mayıs 2026 yürürlük, 13 Mayıs 2026 güncelleme.
- Draft London Plan: 16 Temmuz 2026 tarihli draft; istişare 15 Ekim 2026 17:00'ye kadar.
- MD3515: 13 haftalık statutory consultation kaydı.
- Enfield: examination aktif; 15 Haziran 2026 Inspector güncellemesi ve 3 Temmuz 2026 heritage board bağlamı.
- Havering: mevcut plan 2021 kabul edilmiş; güncelleme evidence-review aşamasında.
- Lambeth: notice 16 Temmuz 2026; preparation beklenen tarih 31 Ekim 2026; hedef adoption 30 Nisan 2029.

## Güvenlik

Kesin parsel bağı, business satırı, skor ve güven üretilmedi. Tüm örnekler `future_growth_score=null`, `confidence_pct=0`, `data_status=NO_DATA` durumundadır. Yeni runner, paralel görev, veritabanı yazımı, migration veya production deploy yapılmadı.

## Engel

Canlı 120-sonuç export'u henüz GitHub'a commit edilmedi. Mevcut ortamın DNS/parametreli URL kısıtı ve canonical single-runner stale heartbeat durumu sürüyor. Manual action sonuçlar commit/readback ve primary-source cross-check tamamlanana kadar açık kalmalıdır.
