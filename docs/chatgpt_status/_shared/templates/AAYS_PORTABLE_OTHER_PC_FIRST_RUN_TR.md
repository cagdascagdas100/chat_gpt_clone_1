# AAYS Portable - Baska Bilgisayarda Ilk Calistirma

1. Portable diski Windows bilgisayara takin.
2. Diskin adi veya harfi ne olursa olsun disk kokundeki `BASKA_BILGISAYARDA_AAYS_BASLAT.cmd` dosyasina cift tiklayin.
3. Bu dosya portable kokunu otomatik bulur, 21-slot on kontrolunu yapar, uygulamayi `8012` portunda baslatir, tek coordinator'i acar ve kontrol panelini gosterir.
4. Masaustu kisayollari icin bir kez `AAYS_KISAYOLLARINI_BU_BILGISAYARA_KUR.cmd` dosyasina cift tiklayin.
5. Disk baska bir harf alirsa eski masaustu kisayolunu kullanmayin; kurucuyu diskten yeniden calistirin.

Sabit baglantilar:

- Uygulama: `http://127.0.0.1:8012/england_map_web/index.html`
- Health: `http://127.0.0.1:8012/health`
- OpenAPI: `http://127.0.0.1:8012/openapi.json`

Notlar:

- Ikinci coordinator acilmaz; mevcut canli coordinator kullanilir.
- Panel kopyasi zaten aciksa yeni panel penceresi acilmaz.
- Bilgisayara kalici otomatik baslatma kurulmaz.
- Log ve durum kanitlari portable disk altindaki `logs` ve `state` klasorlerine yazilir.
- Bu sistem 21 mantiksal slotu korur. Fiziksel eszamanlilik bilgisayarin RAM/CPU profilinden otomatik belirlenir.
- Gercek veri kaniti olmadan `final_ready=true`, sahte tamamlanma veya sahte skor yazilmaz.
