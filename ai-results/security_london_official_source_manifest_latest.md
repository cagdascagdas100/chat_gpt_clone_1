# Security London official source manifest status

- task_id: security-asayis-london-official-source-manifest-20260610
- repo_root: C:\AAYS_GITHUB_BRIDGE_CLEAN2
- work_root: F:\chatgpt\AAYS_WORK\security_asayis_london_official_sources_20260610
- f_drive_available: True
- candidate_count: 15
- parcel_candidate_count: 2
- boundary_candidate_count: 0
- crime_candidate_count: 11
- decision: OFFICIAL_SOURCE_MANIFEST_READY_FOR_REVIEW
- next_step: Create targeted download task for parcel polygons, London boundaries, and crime records from validated candidates; do not mark FINAL_READY.

## Probes
- police_uk_bulk: HEAD_OK 200 - https://data.police.uk/data/
- police_uk_api_docs: HEAD_OK 200 - https://data.police.uk/docs/method/crime-street/
- ons_open_geography: HEAD_OK 200 - https://geoportal.statistics.gov.uk/
- hmlr_inspire: HEAD_OK 200 - https://use-land-property-data.service.gov.uk/datasets/inspire
- london_datastore_recorded_crime: HEAD_FAILED  - https://data.london.gov.uk/dataset/recorded_crime_summary
- gov_uk_imd: HEAD_OK 200 - https://www.gov.uk/government/collections/english-indices-of-deprivation

## Safety
- db_write: false
- production_deploy: false
- ddl: false
- migration: false
- fake_data: false