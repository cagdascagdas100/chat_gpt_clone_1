# AAYS / TerraYield DB Readiness + Canonical Runtime Registry Report

GeneratedAt: 2026-05-15T02:40:06

## 1. Net Durum

Kısmen Uygulandı / Read-only doğrulandı.

Source confidence entegrasyonu branch üzerinde doğrulandı. Docker içindeki local PostGIS runtime read-only olarak doğrulandı. Dış uygulama bağlantısı / .env resolver hedefi hâlâ yanlış porta veya yanlış auth hedefine gidebiliyor.

## 2. Repo / Branch / HEAD

- Repo: C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence
- Remote: https://github.com/cagdascagdas100/chat_gpt_clone_1
- Branch: security-accuracy-expansion-20260508
- HEAD: 2cf89896 Standardize source confidence metadata payloads

Recent commits:
2cf89896 Standardize source confidence metadata payloads
37b33ff5 Wire source confidence into core pipelines
a957f5d5 Add source confidence integration adapter

## 3. Source Confidence Validation

Targeted test result: 27 passed

Validated commits:
- a957f5d5 Add source confidence integration adapter
- 37b33ff5 Wire source confidence into core pipelines
- 2cf89896 Standardize source confidence metadata payloads

## 4. DB Readiness Summary

Docker container içinden read-only probe başarılı oldu.

- Container: terrayield_land_postgis
- Image: postgis/postgis:16-3.4
- Port mapping: 0.0.0.0:55460 -> 5432/tcp
- Target DB: terrayield_land
- Read-only guard: on
- PostgreSQL: 16.4
- PostGIS: 3.4.3

## 5. PostGIS / Geometry Evidence

- public.parcels: centroid, geom, geometry; SRID 27700
- public.parcels_inspire: centroid, geometry; SRID 27700
- public.listings_government_property_finder: point_geometry, site_geometry; SRID 27700
- public.listings_landhub: geometry; SRID 27700
- public.listings_market_adapter: point_geometry, site_geometry; SRID 27700
- public.future_growth_features: centroid, geometry; SRID 27700
- public.city_growth_vectors: geometry set; SRID 4326

Conclusion: PostGIS is required and present in the verified local Docker runtime.

## 6. Domain Tables Observed

Parcel-like: contractor_parcel_match, listing_parcel_link, parcel_context_metric_details, parcel_context_summary, parcel_cost_estimates, parcel_cost_material_lines, parcel_future_growth_evidence, parcel_future_growth_scores, parcel_sales_history, parcel_signal_summary, parcel_verified_sales_history, parcels_inspire.

Cost-like: cost_material_intensity, cost_material_prices, cost_rate_cards, cost_run_logs, cost_source_registry, parcel_cost_estimates, parcel_cost_material_lines, transactions_price_paid.

Contractor-like: contractor_company, contractor_parcel_match, contractor_project, contractor_provenance_evidence.

## 7. Important Auth / Target Finding

External psql through current host env failed against localhost:5432 / user postgres with password authentication failed.

Docker container read-only exec succeeded against container terrayield_land_postgis and database terrayield_land.

Interpretation: The local Docker PostGIS runtime is valid, but the host-side resolver/env target is not aligned with the verified runtime.

## 8. Canonical DB Resolver Policy

Recommended resolver order: TYLI_DATABASE_URL -> DATABASE_URL -> PGHOST/PGPORT/PGDATABASE/PGUSER/PGPASSWORD.

For local Docker runtime, the canonical target should resolve to host localhost, port 55460, database terrayield_land, engine PostgreSQL + PostGIS.

Secret values must remain masked and must not be committed.

## 9. Safety Compliance

Completed read-only: repo/branch/HEAD check, source confidence tests, masked secret presence check, Docker container discovery, Docker exec read-only DB inventory, PostGIS extension/version check, geometry inventory, domain table inventory, index inventory.

Not performed: no migration apply, no production deploy, no runner queue mutation, no secret write/update, no production DB write, no DDL/index create/drop, no destructive cleanup, no git prune/gc cleanup.

## 10. BLOCKED_BY List

- BLOCKED_BY_EXTERNAL_DB_AUTH_TARGET_ALIGNMENT
- BLOCKED_BY_DB_TARGET_APPROVAL_FOR_MANAGED_OR_SELF_HOSTED_PRODUCTION
- BLOCKED_BY_PRODUCTION_MIGRATION_APPROVAL
- BLOCKED_BY_PROD_DEPLOY_APPROVAL

## 11. Current Conclusion

Canlıya Hazır Değil.

Local Docker PostGIS readiness is verified, but production/managed DB target and host-side resolver alignment still require approval and correction.

## 12. Next Single Action

Fix local session/runtime resolver alignment so TYLI_DATABASE_URL or PG env points to the verified Docker PostGIS target on localhost:55460, without printing or committing secret values.
