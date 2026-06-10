# Security London boundary resolver plan

- page_scope: security/asayis London-only pilot
- repo: cagdascagdas100/chat_gpt_clone_1
- branch: main
- generated_at: 2026-06-10T18:20:00+03:00
- decision: `BOUNDARY_RESOLVER_PLAN_READY`

## Evidence reviewed

- Source restore found `ons_open_geography` as `boundary_or_lsoa` with `HEAD_OK` and HTTP 200.
- Official target plan had `boundary_target_count = 0`, so it could not move directly to London extraction/build.

## Boundary resolver decision

Use ONS Open Geography Portal as the official boundary discovery root for London boundary / LSOA / LAD lookup resolution:

- source_id: `ons_open_geography`
- role: `boundary_or_lsoa`
- url: `https://geoportal.statistics.gov.uk/`
- status: `PLAN_READY_NOT_DOWNLOADED`

This is not FINAL_READY. It is a controlled plan artifact that enables the next London-only extraction/build-prep task. No fake data, DB write, DDL, migration, or production deploy is allowed.

## Next required output

- London-only extraction/build-prep task using:
  - HMLR INSPIRE parcel/title polygon targets
  - Police.uk crime targets
  - ONS Open Geography boundary discovery root
- Expected concrete outputs remain:
  - London boundary extract or lookup manifest
  - London parcel/security GeoJSON candidates
  - frontend/build readiness status

## Safety

- db_write: false
- production_deploy: false
- ddl: false
- migration: false
- fake_data: false
- london_only: true
