# Internet F Artifact Headers

## Verified file paths

- `F:\chatgpt\AAYS_WORK\internet_access_score10_real_build_20260610\processed\parcel_internet_access_scores.geojson`
- `F:\chatgpt\AAYS_WORK\internet_access_score10_real_build_20260610\processed\parcel_internet_access_scores.csv`
- `F:\chatgpt\AAYS_WORK\internet_access_score10_real_build_20260610\processed\parcel_internet_access_factor_breakdown.csv`
- `F:\chatgpt\AAYS_WORK\internet_access_score10_real_build_20260610\manifests\calculation_manifest.json`

## Sizes seen by Codex

- `parcel_internet_access_scores.geojson` about `53,796,016` bytes
- `parcel_internet_access_scores.csv` about `72,875,114` bytes
- `parcel_internet_access_factor_breakdown.csv` about `63,959,635` bytes

## GeoJSON head sample

```json
{
  "features": [
    {
      "properties": {
        "source_unit_id": "E00000001",
        "source_unit_type": "postcode",
        "parcel_id": "E00000001",
        "parcel_match_status": "postcode_unit_official_ofcom_no_fake_geometry",
        "internet_access_score_10": 5.045,
        "source_dataset": "Ofcom Connected Nations 2024 fixed coverage",
        "source_file": "F:\\chatgpt\\AAYS_WORK\\internet_access_score10_real_build_20260610\\raw\\extracted\\ofcom_connected_nations_2024\\202407-fixed-coverage-output-areas\\202407_fixed_oa_coverage_r01.csv",
        "fake_data": "false"
      },
      "type": "Feature",
      "geometry": null
    }
  ]
}
```

Ana problem:
- `geometry: null`
- `parcel_id` gercek parcel key gibi degil, postcode birim gibi gozukuyor

## Factor breakdown head sample

```csv
"source_unit_id","parcel_id","source_unit_type","source_dataset","source_file","fake_data"
"E00000001","E00000001","postcode","Ofcom Connected Nations 2024 fixed coverage","F:\chatgpt\AAYS_WORK\internet_access_score10_real_build_20260610\raw\extracted\ofcom_connected_nations_2024\202407-fixed-coverage-output-areas\202407_fixed_oa_coverage_r01.csv","false"
```

Ana problem:
- factor table icin gereken measured value / contribution / confidence alanlari yok

## Manifest summary

```json
{
  "migration": false,
  "db_write": false,
  "production_deploy": false,
  "geometry_policy": "null geometry only; no fake coordinates",
  "task_id": "internet-access-100-transform-ofcom-processed-package",
  "status": "PROCESSED_PACKAGE_READY_POSTCODE_LEVEL_OFFICIAL_SOURCE",
  "fake_data": false
}
```

Ana problem:
- paket resmi kaynakli ama parcel thematic layer son urunu degil
