# Internet Access Kabul Testleri

## A. Statik Testler

```powershell
Set-Location C:\Users\cagda\Documents\GitHub\AAYS
node --check .\england_map_web\app.js
node --check .\england_map_web\internet_access_overlay.js
```

```powershell
Set-Location C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence
python -m py_compile app\api\routes\map_layers.py
```

## B. Veri Varligi Testleri

```powershell
Test-Path E:\AAYS_DATA\internet_access
Test-Path E:\AAYS_DATA\internet_access\processed\parcel_internet_access_scores.csv
Test-Path E:\AAYS_DATA\internet_access\processed\parcel_internet_access_scores.geojson
Test-Path E:\AAYS_DATA\internet_access\reports\internet_access_parcel_report.xlsx
```

Docker DB calisiyorsa:

```powershell
docker exec terrayield_land_postgis psql -U postgres -d terrayield_land -c "select count(*) from parcel_internet_access_scores;"
```

## C. API Contract Testi

```powershell
$BASE = "http://127.0.0.1:8010"
$r = Invoke-RestMethod "$BASE/map/internet-access?bbox=-0.50,51.20,0.30,51.80&limit=20"
$r.type
$r.features.Count
$r.features[0].properties
```

Beklenen:

- `type = FeatureCollection`
- Her parcel en fazla bir feature olarak doner.
- Geometry parcel polygon/multipolygon olur.
- `internet_access_pct`, `internet_access_level_5`, `color_category`, `confidence_level_4`, `source_date`, `matching_method`, `calculation_explanation` vardir.
- `factor_breakdown` array'i veya detail endpoint linki vardir.
- `internet_layer_mode=sales_history_proxy` ise production acceptance fail olmalidir.

## D. UI Kabul Testi

1. Uygulama acilir.
2. Internet ikonuna tiklanir.
3. Buton aktif gorunur.
4. Parcel'lar 5 seviyeli renk skalasiyla gorunur.
5. Legend gorunur.
6. Bir parcel'a tiklanir.
7. Popup veya sag panelde su alanlar gorunur:
   - Internet Access Quality: `%`
   - Very Low/Low/Medium/High/Very High level
   - color category
   - confidence level
   - source list
   - last update/source date
   - matching method
   - explanation
   - factor contribution table
8. Ikona tekrar tiklaninca katman kapanir ve diger layer'lar bozulmaz.

## E. Excel Report Kabul Testi

Beklenen dosya:

```text
E:\AAYS_DATA\internet_access\reports\internet_access_parcel_report.xlsx
```

Workbook sheetleri:

- Summary
- Parcel Scores
- Factor Breakdown
- Sources
- Data Quality
- Diagnostics

Parcel Scores zorunlu kolonlari:

- parcel_id
- parcel_ref
- postcode
- local_authority
- internet_access_pct
- internet_access_level_5
- color_category
- confidence_level_4
- confidence_score_pct
- source_list
- source_dates
- matching_method
- match_geography_level
- calculation_explanation

## F. Kabul Edilmeyecek Durumlar

- Ikon calisiyor ama veri yok.
- Proxy sales-history skoruyla internet katmani tamam sayiliyor.
- Tum parcel'lar ayni renk veya sabit skorla gorunuyor.
- Her faktor ayri feature olup ayni parcel haritada tekrarlaniyor.
- Popup sadece skor gosteriyor, kaynak/faktor/confidence yok.
- Excel raporu yok.
- E-drive kaynak manifesti yok.

