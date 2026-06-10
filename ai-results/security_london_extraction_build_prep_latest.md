# Security London extraction/build-prep plan

- page_scope: security/asayis London-only pilot
- repo: cagdascagdas100/chat_gpt_clone_1
- branch: main
- generated_at: 2026-06-10T18:40:00+03:00
- decision: EXTRACTION_BUILD_PREP_PLAN_READY
- final_ready: false

## Inputs reviewed

- official target plan: `ai-results/security_london_official_target_plan_latest.json`
- boundary resolver plan: `ai-results/security_london_boundary_resolver_plan_latest.json`
- target review: `docs/chatgpt_status/security_london_target_plan_review_20260610.md`

## Selected official source families

- Parcel/title polygons: HMLR INSPIRE candidate URLs.
- Crime/security data: Police.uk target family from official target plan.
- Boundary/lookup: ONS Open Geography discovery root.

## Planned work root

`F:\chatgpt\AAYS_WORK\security_asayis_london_extraction_build_prep_20260610`

## Planned concrete outputs

- London boundary candidate GeoJSON under F-drive work root.
- London parcel candidate GeoJSON under F-drive work root.
- London crime/security candidate JSON or GeoJSON under F-drive work root.
- Repo data targets only after validation:
  - `england_map_web/data/parcel_security_scores_rechecked_0_120m_spatial.geojson`
  - `england_map_web/data/parcel_security_scores_polygons.geojson`

## Remaining blockers

FINAL_READY remains false until concrete London-only boundary, parcel/security GeoJSON artifacts and frontend/smoke status exist.

## Safety

- db_write: false
- production_deploy: false
- ddl: false
- migration: false
- fake_data: false
- london_only: true
