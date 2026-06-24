# Internet Access API/UI Cikti Sozlesmesi

## Layer Endpoint

Mevcut endpoint korunabilir:

```text
GET /map/internet-access?bbox={west,south,east,north}&limit=5000&min_score=&max_score=&region=&local_authority=
```

Response:

```json
{
  "type": "FeatureCollection",
  "features": [],
  "metadata": {
    "layer_kind": "internet_access",
    "source_contract_version": "internet_access_v1",
    "feature_count": 0,
    "data_mode": "official_or_verified",
    "bbox": [-0.5, 51.2, 0.3, 51.8]
  }
}
```

Her feature tek bir parcel polygon/multipolygon olmalidir. Faktor satirlari ayni parcel'i haritada tekrar feature olarak uretmemelidir.

## Feature Properties Zorunlu Alanlari

- `layer_kind`: `internet_access`
- `parcel_id`
- `parcel_ref`
- `local_authority`
- `postcode`
- `internet_access_pct`
- `internet_access_score_10`
- `internet_access_level_5`
- `color_category`
- `color_hex`
- `confidence_level_4`
- `confidence_score_pct`
- `confidence_reason`
- `source_list`
- `source_date`
- `last_verified_at`
- `matching_method`
- `match_geography_level`
- `geometry_precision_level`
- `calculation_version`
- `calculation_explanation`
- `factor_breakdown`

## 5 Seviyeli Internet Access Scale

- 0-20: `Very Low Internet Access`, renk `#7f1d1d`
- 21-40: `Low Internet Access`, renk `#dc2626`
- 41-60: `Medium Internet Access`, renk `#f59e0b`
- 61-80: `High Internet Access`, renk `#84cc16`
- 81-100: `Very High Internet Access`, renk `#065f46`

## 4 Seviyeli Confidence Scale

- `Very High Confidence`: official source + UPRN/postcode exact match + recent source + high geometry precision + >=3 independent factors
- `High Confidence`: official source + postcode/OA match + recent source + >=2 independent factors
- `Medium Confidence`: official source but OA/LSOA/MSOA/local-authority proxy or partial source recency
- `Low Confidence`: regional/local-authority proxy, stale source, weak geometry or limited factor count

## Faktor Breakdown

Her parcel icin faktor tablosu:

```json
[
  {
    "factor_name": "gigabit_coverage",
    "measured_value": "89%",
    "normalized_0_100": 89,
    "weight": 0.25,
    "contribution": 22.25,
    "source_name": "Ofcom Connected Nations Spring 2026",
    "source_url": "https://www.ofcom.org.uk/phones-and-broadband/coverage-and-speeds/connected-nations-update-spring-2026",
    "source_date": "2026-01-01",
    "confidence_level": "High Confidence",
    "evidence_ref": "raw/ofcom/..."
  }
]
```

## Onerilen Faktor Agirliklari

Proje icinde onayli eski scale bulunursa o kullanilmali. Yoksa varsayilan:

- Gigabit-capable / full-fibre coverage: 25%
- Superfast broadband availability: 15%
- Decent broadband gap risk: 15%
- Average/maximum download speed: 15%
- Upload speed: 8%
- Mobile 4G coverage: 8%
- Mobile 5G coverage: 6%
- Provider availability/reliability: 5%
- Broadband infrastructure distance or BDUK future plan: 3%

Toplam 100 olacak sekilde normalize edilmeli. Veri yoksa faktor katkisi uretilmemeli; explanation icinde insufficient evidence yazilmali.

## Popup / Sag Panel

Parcel tiklandiginda gorunmesi gereken minimum:

- `Internet Access Quality: 76%`
- `Level: High Internet Access`
- `Color Category: High / green`
- `Confidence: High Confidence (82%)`
- `Sources: Ofcom, ONSPD, OS Open UPRN, BDUK ...`
- `Last update: 2026-01-01` veya kaynak tarihleri
- `Matching method: postcode_exact / uprn_to_parcel / OA_proxy / LA_proxy`
- Faktor breakdown tablosu
- Hesaplama aciklamasi

## Empty Data ve Proxy Kurali

Veri yoksa:

- Ozellik tamam sayilmaz.
- Endpoint `features: []` + `metadata.warning` + import-ready schema referansi dondurur.
- Overlay sales-history proxy kullanirsa popup/panel bunu `internet_layer_mode=sales_history_proxy` olarak acikca etiketlemeli.
- Production acceptance icin proxy mode kabul edilmemelidir.

## Excel Report Contract

Export path:

```text
E:\AAYS_DATA\internet_access\reports\internet_access_parcel_report.xlsx
```

Workbook sheets:

- Summary
- Parcel Scores
- Factor Breakdown
- Sources
- Data Quality
- Diagnostics

Zorunlu kolonlar `templates/internet_access_excel_workbook_schema.json` icinde tanimlidir.

