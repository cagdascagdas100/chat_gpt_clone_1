# AAYS Future Growth - 21 Slot Sozlesmesi

## Kapsam

Future Growth katmani mevcut 92.283 satirlik Londra kanonik parsel matrisi uzerinde calisir. Bu sayi tum Ingiltere parsel envanteri degildir. Ulusal envanter kurulana kadar Ingiltere geneli tamamlanma iddiasi kullanilmaz.

## Slotlar

- `future_growth_1`: satir 1-30.761
- `future_growth_2`: satir 30.762-61.522
- `future_growth_3`: satir 61.523-92.283

Her slot yalniz kendi `docs/chatgpt_status/aays1/shards/<slot_id>`, `docs/chatgpt_status/_shared/slots_21/<slot_id>` ve `england_map_web/data/aays_21_slots/<slot_id>` koklerine yazabilir. Tek coordinator ve tek Git publisher kullanilir.

## Satir Sozlesmesi

Her kanonik parsel icin bir satir bulunur. Satir en az `program_parcel_id`, parsel geometrisi veya kanonik geometri referansi, `future_growth_score`, `confidence_pct`, `growth_band`, `forecast_horizon`, bilesen puanlari, kaynak URL/tarih, baglama yontemi, olcum seviyesi ve `data_status` alanlarini tasir.

Kanit yetersizse satir korunur fakat `future_growth_score=null`, `confidence_pct=0` ve `data_status=NO_DATA` yazilir. Bolge/postcode/yerel yonetim verisi `AREA_LEVEL_PROXY` olarak etiketlenir; parselde olculmus gercek gibi gosterilmez.

## Kanit ve Puanlama

Puan yalniz kaynakli bilesenlerden hesaplanir: resmi planlama/tahsis, dogrulanmis proje akisi, planlanan ulasim ve altyapi, yapilasma yonu, kentsel dokuya yakinlik ve parsel gelistirilebilirligi. Sel, koruma alani, Green Belt, topografya, cevresel yuk ve hukuki kisitlar ayri ceza bilesenleridir.

`future_growth_score` gelisim tahminidir; `confidence_pct` kaynak kalitesi ve mekansal baglama guvenidir. Bu iki deger birbirinin yerine kullanilmaz. AI yalniz kanit destek aracidir; kaynak veya mekansal eslesme yerine puan uyduramaz.

## Guvenlik

- `fake_data=false`
- `db_write=false`
- `migration=false`
- `production_deploy=false`
- `final_ready=false`

Gercek kaynak, commit, push, remote readback ve tarayici kabul kaniti olmadan PASS, completed veya yuzde 100 yazilmaz.
