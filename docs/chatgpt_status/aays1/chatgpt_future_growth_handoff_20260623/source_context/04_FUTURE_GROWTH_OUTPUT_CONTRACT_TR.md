# Parcel Future Growth Output Contract

Katman adi: `Parcel Future Growth Potential`

Prompt alanlari:

- `Future Growth Value`
- `Future Growth Probability`

## Temel semantik

`future_growth_percent`: 0-100 arasi gelisim potansiyeli sinyali. Kesin fiyat tahmini veya yatirim tavsiyesi degildir.

`growth_probability_percent`: Kalibre edilmis olasilik alanidir. Backtest/ground-truth yoksa `null` kalmali ve `probability_status = probability_not_calibrated` olmalidir.

`confidence_score`: Kaynak ve kanit guveni. Probability yerine kullanilamaz.

## Zorunlu alanlar

| Alan | Tip | Aciklama |
| --- | --- | --- |
| `parcel_id` | int/string | Parsel ID |
| `layer_name` | string | `Parcel Future Growth Potential` |
| `future_growth_percent` | number/null | 0-100 potential score |
| `growth_probability_percent` | number/null | Kalibre edilmis probability, yoksa null |
| `probability_status` | string | `calibrated`, `probability_not_calibrated`, `no_data` |
| `confidence_score` | number/null | 0-100 evidence confidence |
| `color_class` | string | Renk sinifi |
| `hex_color` | string | Harita rengi |
| `score_breakdown` | object | planning, transport, market, demographic, social, policy, risk penalty |
| `top_reasons` | array | Ana pozitif/negatif nedenler |
| `evidence` | array | Parsel-spesifik kanit satirlari |
| `source_title` | string | Kanit kaynagi |
| `source_publisher` | string | Kaynak yayincisi |
| `source_url` | string/null | Kaynak linki |
| `data_date` | date/null | Veri tarihi |
| `publication_date` | date/null | Yayin tarihi |
| `relation_type` | string | INTERSECTS_PARCEL, WITHIN_250M, SAME_LSOA vb. |
| `relation_label` | string | UI etiketi |
| `distance_m` | number/null | Varsa mesafe |
| `impact_weight` | number | Etki agirligi |
| `geography_level` | string/null | PARCEL, SITE, LSOA, LOCAL_AUTHORITY vb. |
| `display_warning` | string/null | Geografi seviyesi uyarisi |
| `calculation_explanation` | string | Hesaplama ve "not price prediction" aciklamasi |
| `calculation_version` | string | Ornek `future_growth_v1` |
| `horizon_years` | int | Ufuk yili |
| `calculated_at` | datetime/null | Hesaplama tarihi |
| `no_data_reason` | string/null | Veri yoksa sebep |

## Renk skalasi

| Aralik | Class | Renk | Hex |
| --- | --- | --- | --- |
| 0-20 | `decline_very_high` | Dark red, decline/weak potential | `#7f1d1d` |
| 20-40 | `decline_risk` | Red-orange, risky/low growth | `#d9480f` |
| 40-55 | `stagnant` | Yellow, stable | `#f4d35e` |
| 55-70 | `limited_growth` | Light green, limited growth | `#9fd356` |
| 70-85 | `strong_growth` | Green, strong growth | `#2f9e44` |
| 85-100 | `breakout_growth` | Blue, very high/jump potential | `#1f6feb` |
| null | `no_data` | Gray/transparent | `#6b7280` |

## Skor formulu

```text
future_growth_percent =
  30% planning_growth_score
+ 20% transport_infra_score
+ 15% market_momentum_score
+ 15% demographic_demand_score
+ 10% social_amenity_score
+ 10% land_supply_and_policy_score
- risk_penalty
```

## Popup/panel zorunlu aciklama

Popup/panelde su tur aciklama bulunmali:

```text
This is not a guaranteed price prediction. It is a future growth potential signal based on planning, transport, market momentum, demographic demand, social amenities, land supply, and policy/risk factors.
```

## Final GeoJSON/API

`/api/future-growth/layer` FeatureCollection donmeli:

- `geometry`: parcel polygon/multipolygon veya zoom dusukse point olabilir; final accepted high zoom parcel view'da polygon beklenir.
- `properties.parcel_id`
- `properties.future_growth_percent`
- `properties.confidence_score`
- `properties.color_class`
- `properties.hex_color`

`/api/future-growth/parcels/{parcelId}` detail donmeli:

- breakdown
- evidence
- warnings
- sources
- calculation metadata
