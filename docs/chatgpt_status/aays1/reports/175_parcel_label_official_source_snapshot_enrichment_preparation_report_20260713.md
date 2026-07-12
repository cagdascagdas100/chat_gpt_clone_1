# Task 175 — Parcel Label Official Source Snapshot Enrichment — Preparation Report

## Scope

- Existing Parcel Label rows selected: **6**
- New candidate rows: **0**
- Planned average accuracy: **3.858/4**
- Exact geometry created by preparation: **0**
- Canonical execution: existing F portable single shared runner only

## Selected existing rows

1. Westfield London — Retail Property — 3.95/4
2. The News Building — Office Building — 3.85/4
3. The Shard — Mixed Building — 3.95/4
4. One Hyde Park — Apartment Building — 3.75/4 — manual review retained
5. Witanhurst — Detached Home — 3.95/4
6. SEGRO Park Dagenham / London Sustainable Industries Park — Industrial Unit — 3.70/4 — specific unit binding required

## Planned row-level outputs

For every updated row, Task 175 will publish the source URL and all available source snapshot, input, queue, evidence, report and runner-output paths. The row will be marked `SOURCE_AND_ADDRESS_ENRICHED` while `geometry_status=NOT_BOUND` remains unchanged until exact building or parcel evidence exists.

## Current proven baseline

- Unique tracked parcels: **194**
- Browser-visible unique parcels: **194**
- Site visibility: **100%**
- Pending runner rows: **188**
- GeoJSON features: **6**
- Local-present row artifacts: **846**
- Missing row artifacts: **706**

## Acceptance

Completion requires a real Task 175 runner output, port 8012 HTTP row match and GitHub remote readback. Source pages that reject automated download must be recorded as failed snapshots; they must not be represented as downloaded. No product-final claim is permitted.

`final_ready=false`, `product_final_ready=false`, `fake_data=false`, `db_write=false`, `migration=false`, `production_deploy=false`.
