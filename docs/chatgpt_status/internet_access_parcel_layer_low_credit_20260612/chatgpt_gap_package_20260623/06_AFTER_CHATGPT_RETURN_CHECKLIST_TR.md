# After ChatGPT Return Checklist

ChatGPT patch/runbook dondugunde su sirayla ilerle:

1. Sadece kucuk metin ve scriptleri repo icine al
2. Buyuk veri ve ETL outputlari yalnizca `F:` veya `D:` root altina yaz
3. Fake geometry yok mu kontrol et
4. `parcel_internet_access_scores.geojson` icinde renderable geometry var mi kontrol et
5. `parcel_internet_access_factor_breakdown.csv` contract alanlari tamam mi kontrol et
6. Gerekirse DB import yap
7. `http://127.0.0.1:8010/map/internet-access?...` bos mu degil mi kontrol et
8. Browser'da Internet iconunu ac
9. Parcel polygonlar renklendi mi bak
10. Tiklanan parcellerde popup/right panel alanlari gorunuyor mu bak

Tamamlandi demek icin su 6 sey ayni anda gerekli:

1. icon calisiyor
2. parcel polygonlar gorunuyor
3. color scale gorunuyor
4. popup/right panel alanlari tam
5. factor table tam
6. source/confidence/calculation acik
