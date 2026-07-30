# future_growth_2 live official query manifest

Continuation key: `5c59c5cee91d859c9e09480645ef8b17efe264568f2a4e312dd49d70e2958462`

Generated: `2026-07-30T17:07:00+03:00`

Read-only ArcGIS `returnIdsOnly` point-intersects queries. The 19 official layers below were crossed with all three candidate coordinates, producing 57 actual requests. Transport failure is not a positive or negative membership result.

Transport: 57 attempts; parallelism 57; exit 6 ×57; HTTP 000 ×57; body bytes 0; JSON 0/57; raw-response SHA-256 0/57.

Query manifest SHA-256: `1488ec2d4f3d99b367aaff7e5371433114b9c75f66e6b1e76dc6e70472139849`
Transport results SHA-256: `452aa71e1df78bcb9b7d52d31750c05e35e228477173bf751705aa2071a1a6d3`

## Candidate coordinates

- Row 30762 — Enfield: `535564.9947401143,199388.1084759141`
- Row 46142 — Havering: `551991.914381677,190529.33854737692`
- Row 61522 — Lambeth: `529493.3809399875,170122.18940480007`

## Official layer endpoints

1. PDM 317 — London Context Other Infrastructure: `https://gis.london.gov.uk/arcgis/rest/services/apps/planning_data_map_02/FeatureServer/317`
2. PDM 322 — London Context Setting E: `https://gis.london.gov.uk/arcgis/rest/services/apps/planning_data_map_02/FeatureServer/322`
3. PDM 323 — London Context Setting F: `https://gis.london.gov.uk/arcgis/rest/services/apps/planning_data_map_02/FeatureServer/323`
4. WEBMAP 12 — London Planning Authority: `https://gis.london.gov.uk/arcgis/rest/services/apps/webmap_context_layer/FeatureServer/12`
5. WEBMAP 10 — London Planning Authority (Pre-Dec 2024): `https://gis.london.gov.uk/arcgis/rest/services/apps/webmap_context_layer/FeatureServer/10`
6. WEBMAP 7 — London Assembly Constituencies: `https://gis.london.gov.uk/arcgis/rest/services/apps/webmap_context_layer/FeatureServer/7`
7. WEBMAP 14 — London Westminster Constituencies: `https://gis.london.gov.uk/arcgis/rest/services/apps/webmap_context_layer/FeatureServer/14`
8. WEBMAP 15 — London MPS Basic Command Units: `https://gis.london.gov.uk/arcgis/rest/services/apps/webmap_context_layer/FeatureServer/15`
9. WEBMAP 6 — OPDC: `https://gis.london.gov.uk/arcgis/rest/services/apps/webmap_context_layer/FeatureServer/6`
10. WEBMAP 13 — LLDC: `https://gis.london.gov.uk/arcgis/rest/services/apps/webmap_context_layer/FeatureServer/13`
11. WEBMAP 11 — LLDC (Pre-Dec 2024): `https://gis.london.gov.uk/arcgis/rest/services/apps/webmap_context_layer/FeatureServer/11`
12. WEBMAP 1 — River Thames: `https://gis.london.gov.uk/arcgis/rest/services/apps/webmap_context_layer/FeatureServer/1`
13. WEBMAP 4 — TfL 350m Hexagon Grid: `https://gis.london.gov.uk/arcgis/rest/services/apps/webmap_context_layer/FeatureServer/4`
14. WEBMAP 5 — London Wards (2021): `https://gis.london.gov.uk/arcgis/rest/services/apps/webmap_context_layer/FeatureServer/5`
15. WEBMAP 8 — London LSOA (2021): `https://gis.london.gov.uk/arcgis/rest/services/apps/webmap_context_layer/FeatureServer/8`
16. WEBMAP 9 — London Wards (2022): `https://gis.london.gov.uk/arcgis/rest/services/apps/webmap_context_layer/FeatureServer/9`
17. WEBMAP 18 — London Wards (2025): `https://gis.london.gov.uk/arcgis/rest/services/apps/webmap_context_layer/FeatureServer/18`
18. WEBMAP 17 — Oxford Street Mayoral Development Area: `https://gis.london.gov.uk/arcgis/rest/services/apps/webmap_context_layer/FeatureServer/17`
19. WEBMAP 16 — Index of Multiple Deprivation 2025: `https://gis.london.gov.uk/arcgis/rest/services/apps/webmap_context_layer/FeatureServer/16`

## Request template

`{layer_url}/query?where=1%3D1&geometry={x}%2C{y}&geometryType=esriGeometryPoint&inSR=27700&spatialRel=esriSpatialRelIntersects&returnIdsOnly=true&f=json`

All 57 requests are rendered as individual operation rows in `support_audit_wave_41032_41564_20260730.html`.
