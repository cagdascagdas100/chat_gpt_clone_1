# Mevcut Durum Denetimi

Tarih: 2026-06-12

Bu denetim dusuk kredi amaciyla statik repo okuma ve dar kapsamli dosya incelemesiyle yapildi. Docker DB, canli localhost ve veri indirme calistirilmadi.

## Dogrulanan Mevcut Parcalar

Frontend:

- `england_map_web/app.js` icinde `INTERNET_CONTROL_MODE = "__internet_access_toggle__"` mevcut.
- Ana map kontrol item'i Internet katmani icin `./assets/icons/terrayield_icons/internet.png` ikonunu kullaniyor.
- `setInternetLayerVisibility(...)`, `toggleInternetLayer()` ve `window.AAYS_INTERNET` bridge kontrolu mevcut.
- `england_map_web/index.html` su script'i yukluyor:
  - `./internet_access_overlay.js?v=20260525-internet-layer-v1`
- `england_map_web/internet_access_overlay.js` icinde:
  - source/layer id'leri mevcut.
  - varsayilan endpoint `/map/internet-access`.
  - varsayilan fallback GeoJSON `./data/parcel_internet_access_scores.geojson`.
  - 0-10 skor uzerinden renk expression'i mevcut.
  - popup temel skor/kaynak/confidence alanlarini gosteriyor.

Backend:

- `terrayield_land_intelligence/app/api/routes/map_layers.py` icinde `GET /map/internet-access` route'u mevcut.
- Route `parcel_internet_access_scores s` tablosunu `parcels_inspire p` ile join ediyor.
- Route su alanlari dondurmeyi hedefliyor:
  - `internet_access_score_10`
  - `internet_access_pct`
  - `internet_access_level_5`
  - `confidence_level_4`
  - `confidence_score_pct`
  - `confidence_reason`
  - `factor_name`
  - `factor_level`
  - `raw_value`
  - `normalized_0_100`
  - `weight`
  - `contribution`
  - `source_name`
  - `source_url`
  - `source_date`
  - `last_verified_at`
  - `evidence_ref`
  - `calculation_version`

Rapor/dokuman:

- `terrayield_land_intelligence/docs/reports/TerraYield_AAYS_Internet_Katmani_Raporu_20260611.docx` onceki internet katmani raporu olarak mevcut olabilir.
- `docs/reports/build_internet_layer_report_docx.py` internet katmani kaynak ve uygulama mantigini belgeleyen bir script iceriyor.

## Kritik Eksikler

1. Gercek parcel internet veri dosyasi yok.
   - `england_map_web/data/parcel_internet_access_scores.geojson` mevcut degil.

2. Beklenen DB tablosu kesin dogrulanmadi.
   - Route `parcel_internet_access_scores` tablosunu bekliyor.
   - Narrow static taramada bu tablo icin acik model/migration bulunamadi.
   - Docker PostGIS calismadan tablo varligi ve satir sayisi dogrulanmadi.

3. Overlay proxy fallback final davranis icin riskli.
   - Gercek internet verisi yoksa overlay `/map/sales-history/parcels` proxy'sinden skor uretebiliyor.
   - Bu final Internet Access katmani olarak kabul edilmemeli; sadece diagnostic/demo fallback olarak etiketlenmeli veya production acceptance icin kapatilmali.

4. Faktor tablosu UI'da eksik.
   - Route faktor alanlarini dondurebiliyor gibi tasarlanmis.
   - Popup tek faktor satirini metin olarak gosteriyor.
   - Kullanici istegine gore her parcel icin faktor breakdown tablosu gerekir.

5. Veri modeli satir granulerligi belirsiz.
   - Route `parcel_internet_access_scores` tablosunda faktor alanlari ile skor alanlarini ayni satirda bekliyor.
   - Eger her faktor ayri satirsa ayni parcel haritada birden cok feature olarak tekrar edebilir.
   - Daha guvenli tasarim: `parcel_internet_access_scores` ana skor tablosu + `parcel_internet_access_factors` detay tablosu veya JSON array.

6. Excel export yok.
   - Uygulamada tum parcel'lar icin internet access Excel raporu ureten net endpoint/script bu dar denetimde gorulmedi.

7. E-drive veri klasoru sozlesmesi uygulanmamis.
   - Kullanici tum kaynak ve ciktilarin `E:\AAYS_DATA\internet_access\` altinda saklanmasini istiyor.
   - Bu paket klasor yapisi ve runbook saglar; dosyalari E drive'a bu turda yazmadim.

8. Worth menu uyumsuzlugu var.
   - Ana map kontrolu `internet.png` kullaniyor.
   - `MAP_WORTH_MENU_ITEMS` icindeki ikinci `internet` girisi halen `./assets/icons/worth-global.svg` kullaniyor. Bu, hangi internet butonunun final kabul icin kullanildigini belirsizlestirebilir.

## Sonuc

Internet katmani "sadece ikon" seviyesinde degil; overlay ve endpoint kancalari hazir. Fakat gercek data pipeline, parcel match, fallback GeoJSON/DB tablo varligi, faktor breakdown UI, Excel export ve confidence/matching contract'i tamamlanmadan ozellik final kabul kuralina gore tamam sayilmamalidir.

## Bu Pakette Calistirilan Read-only Audit Sonucu

Calistirilan betik:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\terrayield_land_intelligence\docs\chatgpt_handoff\internet_access_parcel_layer_low_credit_20260612\07_LOCAL_READONLY_AUDIT.ps1
```

Ozet:

- `node --check england_map_web\app.js`: basarili.
- `node --check england_map_web\internet_access_overlay.js`: basarili.
- `python -m py_compile app\api\routes\map_layers.py`: basarili.
- `internet.png` dosyasi mevcut ve SHA256: `676997E3C0F0D8F291DCFE28408C5EA155A09F6A135DA606753C0CE116B984F4`.
- `england_map_web\data\parcel_internet_access_scores.geojson`: eksik.
- `E:\AAYS_DATA\internet_access` ve alt klasorleri: eksik.
- Localhost `127.0.0.1:8010` calismadigi icin HTTP endpoint testleri baglanti hatasi verdi.
- Docker container listesinde `terrayield_land_postgis` calismadigi icin DB tablo sayimlari atlandi.
- Zorunlu contract hizli kontrolunde eksik gorunen terimler:
  - `factor_breakdown`
  - `matching_method`
  - `calculation_explanation`
  - `color_category`
  - `source_list`
  - `match_geography_level`
  - `geometry_precision_level`
  - `internet_access_parcel_report.xlsx`

Audit raporu paket icinde `audit_output/` altinda saklandi.
