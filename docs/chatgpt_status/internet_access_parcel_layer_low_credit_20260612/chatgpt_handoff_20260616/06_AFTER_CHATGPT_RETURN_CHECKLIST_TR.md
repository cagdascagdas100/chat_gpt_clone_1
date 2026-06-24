# After ChatGPT Return Checklist

ChatGPT donusu geldiginde asagidakilerden biri bile eksikse "tamam" kabul etme:

- `parcel_internet_access_scores_ready.geojson` renderable geometry iceriyor mu?
- geometry hala `null` mu?
- parcel polygon / multipolygon var mi?
- `factor_breakdown` gercekten dolu mu?
- `matching_method` var mi?
- `calculation_explanation` var mi?
- `color_category` var mi?
- `source_list` / `source_date` var mi?
- `internet_access_parcel_report_ready.xlsx` var mi?
- ChatGPT patch dosyalari repo hedefleri icin hazir mi?
- output root `F:` veya `D:` altinda mi?
- proxy mode primary source olarak kalmis mi?

Asagidakiler varsa "eksik" de:

- sadece icon/toggle calisiyor
- sadece percentage var ama parcel geometry yok
- postcode unit data parcel layer gibi gosteriliyor
- GeoJSON satir sayisi yuksek ama geometry yok
- "production complete" denmis ama DB write/import yok

