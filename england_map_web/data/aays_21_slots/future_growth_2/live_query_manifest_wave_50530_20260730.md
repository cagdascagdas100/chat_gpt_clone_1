# future_growth_2 live official query manifest

Continuation key: `5c59c5cee91d859c9e09480645ef8b17efe264568f2a4e312dd49d70e2958462`
Generated: `2026-07-30T22:33:00+03:00`

Read-only official ArcGIS `returnIdsOnly` point-intersects queries. Transport failure is not interpreted as a positive or negative result.

Transport: 135 attempts; parallelism 135; exit counts {'28': 134, '6': 1}; HTTP counts {'000': 135}; body bytes 0; JSON 0/135; raw-response SHA-256 0/135.

Query manifest SHA-256: `c6d45105953d82483288ac03d6abce32002fbf29cf0c77c959d3ecf67e62d215`
Transport results SHA-256: `41a6985aad376d240da3865cd8eaece172a763c9d3ba11ba2640e3d951774b9e`
Layer manifest SHA-256: `d176b0cf28d1665e06fd69ec52195700059c3d93b72da996969295294605fdaf`

Layers crossed with rows 30762, 46142 and 61522:
- LGIF 1 Registered Parks and Gardens (UNRESOLVED, MIRROR, SERVICE_INVENTORY_ONLY)
- LGIF 2 Spaces to Visit 2025 (UNRESOLVED, MIRROR, SERVICE_INVENTORY_ONLY)
- LGIF 3 Ramsar sites (UNRESOLVED, MIRROR, SERVICE_INVENTORY_ONLY)
- LGIF 4 Special Areas of Conservation (UNRESOLVED, MIRROR, SERVICE_INVENTORY_ONLY)
- LGIF 5 Special Protection Areas (UNRESOLVED, MIRROR, SERVICE_INVENTORY_ONLY)
- LGIF 6 Sites of Special Scientific Interest (UNRESOLVED, MIRROR, SERVICE_INVENTORY_ONLY)
- LGIF 7 Area private garden per 1,000 people (UNRESOLVED, NEW, SERVICE_INVENTORY_ONLY)
- LGIF 8 Accessible Waterside (UNRESOLVED, NEW, SERVICE_INVENTORY_ONLY)
- LGIF 9 Fluvial FloodZone 2 (UNRESOLVED, NEW, SERVICE_INVENTORY_ONLY)
- LGIF 10 Fluvial FloodZone 3 (UNRESOLVED, NEW, SERVICE_INVENTORY_ONLY)
- LGIF 11 Misconnection Points (UNRESOLVED, NEW, SERVICE_INVENTORY_ONLY)
- LGIF 12 WFD Catchment - length of High-Priority Roads (UNRESOLVED, NEW, SERVICE_INVENTORY_ONLY)
- LGIF 13 Green Riparian Areas (UNRESOLVED, NEW, SERVICE_INVENTORY_ONLY)
- LGIF 14 Daytime Temperature (UNRESOLVED, NEW, SERVICE_INVENTORY_ONLY)
- LGIF 15 Cycle Routes (UNRESOLVED, NEW, SERVICE_INVENTORY_ONLY)
- LGIF 16 Green Cover in High Streets (UNRESOLVED, NEW, SERVICE_INVENTORY_ONLY)
- LGIF 17 Social inequalities - under 5 years (UNRESOLVED, NEW, SERVICE_INVENTORY_ONLY)
- LGIF 18 Social inequalities - over 75 years (UNRESOLVED, NEW, SERVICE_INVENTORY_ONLY)
- LGIF 19 Social inequalities - not proficient English (UNRESOLVED, NEW, SERVICE_INVENTORY_ONLY)
- LGIF 20 Social inequalities - social housing (UNRESOLVED, NEW, SERVICE_INVENTORY_ONLY)
- LGIF 21 Social inequalities - BAME (UNRESOLVED, NEW, SERVICE_INVENTORY_ONLY)
- LGIF 22 IMD 2019 - 20% most Income Deprived (UNRESOLVED, NEW, SERVICE_INVENTORY_ONLY)
- LGIF 23 IMD 2019 - Health Deprivation and Disability (UNRESOLVED, NEW, SERVICE_INVENTORY_ONLY)
- LGIF 24 Priority Areas (UNRESOLVED, NEW, SERVICE_INVENTORY_ONLY)
- BUSY 12 Mastercard grid (esriGeometryPolygon, NEW, COMPLETE_LAYER_EXTENT)
- BUSY 11 TfL 350m hex grid (UNRESOLVED, MIRROR, SERVICE_INVENTORY_ONLY)
- BUSY 0 London Borough (UNRESOLVED, MIRROR, SERVICE_INVENTORY_ONLY)
- BUSY 1 Business Improvement Districts (esriGeometryPolygon, REPRESENTATION, COMPLETE_LAYER_EXTENT)
- BUSY 2 Central Activities Zone (UNRESOLVED, MIRROR, SERVICE_INVENTORY_ONLY)
- BUSY 3 High Streets (esriGeometryPolygon, NEW, COMPLETE_LAYER_EXTENT)
- BUSY 4 MSOA boundaries (esriGeometryPolygon, NEW, COMPLETE_LAYER_EXTENT)
- BUSY 5 Town Centres (esriGeometryPolygon, MIRROR, COMPLETE_LAYER_EXTENT)
- BUSY 8 Borough Bespoke Areas (esriGeometryPolygon, NEW, COMPLETE_LAYER_EXTENT)
- BIDS 0 BIDs (esriGeometryPolygon, MIRROR, COMPLETE_LAYER_EXTENT)
- BIDS 6 London boroughs (UNRESOLVED, MIRROR, SERVICE_INVENTORY_ONLY)
- BIDS 8 BID_crp_web (esriGeometryPolygon, REPRESENTATION, COMPLETE_LAYER_EXTENT)
- SOCIAL 0 Social housing postcode local-authority lookup (UNRESOLVED, NEW, SERVICE_INVENTORY_ONLY)
- SUDS 3 Thames Water Combined Sewer (esriGeometryPolygon, NEW, COMPLETE_LAYER_EXTENT)
- SUDS 4 Thames Water Separate Sewer (esriGeometryPolygon, NEW, COMPLETE_LAYER_EXTENT)
- SUDSSUB 1 Approved SuDS site (UNRESOLVED, NEW, SERVICE_INVENTORY_ONLY)
- SUDSSUB 0 Add new SuDS site (UNRESOLVED, NEW, SERVICE_INVENTORY_ONLY)
- SURVEY 0 London Assembly constituencies (UNRESOLVED, MIRROR, SERVICE_INVENTORY_ONLY)
- LOCALPLAN 301 London Borough (UNRESOLVED, MIRROR, SERVICE_INVENTORY_ONLY)
- NEIGH 0 NeighbourhoodAreas_map (esriGeometryPolygon, NEW, COMPLETE_LAYER_EXTENT)
- SSSB 0 Small sites - point (esriGeometryPoint, NEW, COMPLETE_POINT_LAYER_EXTENT)

Every request used the official layer `/query` endpoint with `where=1=1`, point geometry, `esriSpatialRelIntersects`, `returnIdsOnly=true`, and `f=json`; EPSG:27700 or EPSG:3857 followed the service declaration.

Inventory-only layers were not assigned fabricated geometry, display fields or layer extents. Point extents, service-root extents, mirrors and representations were not counted as parcel proximity, membership or duplicate exact negatives.

Exact named-layer extent negatives: Enfield 3; Havering 1; Lambeth 0. These are limited to complete eligible named polygon extents and do not establish planning permission, investment, utility capacity or delivery certainty.
