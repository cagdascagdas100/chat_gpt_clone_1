# Security London Source Restore Audit

Completed: 2026-06-10T16:24:04.1515785+03:00
Decision: BLOCKED_NO_LOCAL_PARCEL_OR_SECURITY_GEODATA
Ready for London build: False

## Source probes
- police_uk_api: HEAD_OK 200 - https://data.police.uk/docs/method/crime-street/
- police_uk_bulk: HEAD_OK 200 - https://data.police.uk/data/
- ons_open_geography: HEAD_OK 200 - https://geoportal.statistics.gov.uk/
- hmlr_inspire: HEAD_OK 200 - https://use-land-property-data.service.gov.uk/datasets/inspire
- london_datastore_recorded_crime: FAILED  - https://data.london.gov.uk/dataset/recorded_crime_summary
- gov_uk_imd: HEAD_OK 200 - https://www.gov.uk/government/collections/english-indices-of-deprivation

## Local checks
- expected_point_input: exists=False length= path=C:\AAYS_GITHUB_BRIDGE_CLEAN2\england_map_web\data\parcel_security_scores_rechecked_0_120m_spatial.geojson
- expected_polygon_input: exists=False length= path=C:\AAYS_GITHUB_BRIDGE_CLEAN2\england_map_web\data\parcel_security_scores_polygons.geojson
- f_point_output: exists=False length= path=F:\chatgpt\AAYS_WORK\security_asayis_london_pilot_20260609\data\parcel_security_scores_london_pilot_points.geojson
- f_polygon_output: exists=False length= path=F:\chatgpt\AAYS_WORK\security_asayis_london_pilot_20260609\data\parcel_security_scores_london_pilot_polygons.geojson
- f_summary: exists=True length=5711 path=F:\chatgpt\AAYS_WORK\security_asayis_london_pilot_20260609\data\parcel_security_london_pilot_summary.json

## Safety
- DB write: false
- DDL/migration: false
- Production deploy: false
- Fake data: false
- Scope: London only
