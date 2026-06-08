# AAYS Real Topography Product — Artifact Blocker

STATUS: BLOCKED_WAITING_FOR_REAL_ELEVATION_ARTIFACT

PRODUCT_PROGRESS_ESTIMATE: 82

Confirmed complete:
- UI visibility acceptance is complete.
- app.js popup/cache logic is present for two metrics.
- Backend lookup v2 route was added.
- The lookup contract is structured and must not fabricate values.

Current real blocker:
- `parcel_elevation_lookup_v2.json` or an equivalent real elevation lookup artifact was not found in GitHub search.
- No fake or synthetic elevation artifact should be created.

Required artifact fields:
- `parcel_id`
- `center_elevation_m`
- `region_average_elevation_m`
- `elevation_difference_from_region_average_m`
- `region_sample_count`
- `datum`
- `source_dataset`
- `status`

Required next work:
1. Locate or generate a real `parcel_elevation_lookup_v2.json` from validated elevation source data.
2. Run `/lookup?parcel_id=...` or `/topography/lookup?parcel_id=...` smoke.
3. Run browser popup smoke and prove both real metrics render.

Expected progress:
- Real artifact found/generated and schema-valid: 82 -> 88
- API smoke structured response passes: 88 -> 92
- Browser popup proof passes: 92 -> 100 FINAL_READY

NO_FAKE_DATA_POLICY: ACTIVE
DB_WRITE: FALSE
MIGRATION: FALSE
DEPLOY: FALSE
