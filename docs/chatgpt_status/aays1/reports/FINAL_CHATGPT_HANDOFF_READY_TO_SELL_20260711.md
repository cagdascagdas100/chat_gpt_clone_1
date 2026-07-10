# Ready To Sell / Geometry Review - Çözüm ve Devam Raporu

Bu dosyayı mevcut Ready To Sell ChatGPT sayfasına ver. Sonrasında kullanıcı yalnızca **devam et** yazdığında aynı shared runner üzerinden sürdür.

## Çözülen sorunlar

- Sabit site: `http://127.0.0.1:8012/england_map_web/geometry_review_3of4_columns_1264.html`.
- Canonical geometri, AI evidence, product status ve runner proof dosyaları açık yollarla yükleniyor.
- AI JSON fetch hatası artık sessizce boş sonuç sayılmıyor.
- 1264 geometri satırı ve 30 canlı-kaynak doğrulanmış AI sonucu site verisine bağlandı.
- `Yalnız latest-run / AI sonuçlu` filtresi ve satır seviyesinde kaynak/status/report yolları eklendi.
- Vision kanıtı olmayan satıra 3.5+ yazılmasını engelleyen kural korunuyor.
- HTML UTF-8 sunuluyor; eski bozuk Türkçe HTML metinleri düzeltildi.
- Tek runner smoke testi GitHub push ve remote readback ile geçti: `b45cdc1648574602e237cdcba2b0f03b55935812`.

## Gerçek mevcut durum

- Geometry: `1264`
- Canlı kaynak doğrulanmış AI satırı: `30`
- Fotoğraf indirme + polygon render + vision compare tamamlanan satır: `0`
- 3.5+ olarak doğrulanmış satır: `0`
- `final_ready=false`

## Devam talimatı

1. Yeni runner açma; mevcut shared runner görev ve output dosyalarını kullan.
2. 30 satır için gerçek fotoğraf indirme, canonical polygon render ve vision comparison çıktısını küçük batch'lerle üret.
3. Her satırda indirilen fotoğraf, polygon render, vision output, status ve report yolu görünür olmadan confidence artırma.
4. Mismatch veya eksik kanıt varsa `VISION_PENDING` ya da `MANUAL_REVIEW_REQUIRED` olarak bırak.
5. Sonuçları aynı 8012 sayfasında refresh sonrası görünür hale getir ve GitHub remote readback ile doğrula.
6. Kullanıcı `devam et` dediğinde veri işine devam et; runner altyapısını yeniden kurma.

## Kalan gerçek iş

Ready To Sell ürün işi tamamlanmış değildir. 30 satırın vision zinciri ve kalan 1234 satır gerçek kanıtla işlenmelidir.

Gerçek Chrome/Selenium testi geçti: ilk sayfada 50/1264 satır, latest/AI filtresinde 30/30 satır çizildi; Türkçe UTF-8 ve tarayıcı konsolu temizdi. Browser proof: `docs/chatgpt_status/_shared/reports/five_page_browser_validation_20260711.json`.
