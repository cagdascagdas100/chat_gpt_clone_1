# AAYS Portable Uygulama, Kalıcı Durdurma ve Web Senkron Denetimi - 2026-07-18

## Sonuç
- Sabit uygulama URL: `http://127.0.0.1:8012/england_map_web/index.html`
- Health, OpenAPI, ana web ve iki kontrol sayfası: HTTP 200.
- Uygulama API tabanı: `same-origin`; değişken 8010 bağımlılığı kaldırıldı.
- Sekiz bölgenin local PMTiles kaynağı: 8/8 HTTP range testi PASS.
- PMTiles toplam boyutları sunucu tarafından doğrulandı; veriler F portable kökte ve disk harfinden bağımsız launcher ile servis ediliyor.
- Program matrisi: `chunks/manifest.json` içinde 92.283 satır, 923 chunk.
- Önemli kapsam doğrusu: manifest `london_yes=92283` diyor. 92.283 mevcut Londra program matrisidir; bütün İngiltere parsel toplamı değildir. İngiltere/Wales/Scotland harita geometrileri sekiz bölgesel PMTiles kaynağındadır.
- Parsel poligon tıklama işleyicileri viewport GeoJSON, local fallback, region GeoJSON ve PMTiles fill katmanlarında mevcut.
- Kontrol sitesi senkronu artık önce `runner_system/adaptive_v2/publisher` checkout'unu kullanıyor; tarihsel outputs yoksa legacy checkout'a güvenli fallback yapıyor.
- Son senkron: 0 hata; iki sabit kontrol URL'si çalışıyor.
- Windows'taki eski `AAYS Portable Runner Guardian` görevi devre dışı bırakıldı.
- Durdur testi: STOPPED_CLEAN, PID kapandı, persistent manual-stop yazıldı, 70 saniye sonra kendiliğinden başlamadı.
- Açık Başlat testi: manual-stop kaldırıldı, tek koordinatör PID ile RUNNING; ikinci başlatma kilitle engelleniyor.
- 15 slot manifesti: 15/15. Her slotta ownership/checkpoint/heartbeat/current_task/status: 15/15 mevcut.
- Yeni sayfa promptu UTF-8 olarak düzeltildi; ZIP/sohbet tarihi yerine GitHub HEAD ve slot checkpoint authoritative.
- İki hesap için benzersiz 8+7 slot örnek dağılımı eklendi.

## Test Edilemeyenler / Kalan Blocker
- Fiziksel ikinci Windows bilgisayar bu oturumda bağlı değildi; gerçek tak-çalıştır testi NOT_RUN.
- İngiltere geneli tekil ulusal parsel sayımı mevcut 92.283 Londra matrisiyle karıştırılamaz; ulusal envanter sayımı ayrı gerçek kaynak/iş gerektirir.
- İlk gerçek uzun business task için uçtan uca publisher commit/push/site görünürlük testi bu denetimde yeniden çalıştırılmadı.

`final_ready=false`, `product_final_ready=false`, `fake_data=false`, `db_write=false`, `migration=false`, `production_deploy=false`.
