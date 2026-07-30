# future_growth_2 live official query manifest

Continuation key: `5c59c5cee91d859c9e09480645ef8b17efe264568f2a4e312dd49d70e2958462`
Generated: `2026-07-30T19:13:00+03:00`

Read-only official ArcGIS `returnIdsOnly` point-intersects queries. Transport failure is not interpreted as a positive or negative result.

Transport: 105 attempts; parallelism 105; exit 6 x105; HTTP 000 x105; body bytes 0; JSON 0/105; raw-response SHA-256 0/105.

Query manifest SHA-256: `3cb8c9d0840f531b9ebfec3836872500693ce1f08af6c144152622b744cfb346`
Transport results SHA-256: `0be3356bfab531c42bc57f0530a0a7e18ff208e6e8695099373f6a6145c43627`

Layers crossed with rows 30762, 46142 and 61522:
- WASTE2026 100 all ea waste_sites_points_web (esriGeometryPoint, NEW)
- WASTE2026 714 HIC — Disposal (esriGeometryPoint, NEW)
- WASTE2026 713 HIC — Fuel preparation and MBT (esriGeometryPoint, NEW)
- WASTE2026 712 HIC — Household Reuse and Recycling Centres (esriGeometryPoint, NEW)
- WASTE2026 711 HIC — Materials recycling and sorting (esriGeometryPoint, NEW)
- WASTE2026 710 HIC — Metals and vehicle recycling (esriGeometryPoint, NEW)
- WASTE2026 82 HIC — Organic treatment (esriGeometryPoint, NEW)
- WASTE2026 719 HIC — Other (esriGeometryPoint, NEW)
- WASTE2026 718 HIC — Thermal treatement (esriGeometryPoint, NEW)
- WASTE2026 717 HIC — Transfer and treatment (construction, demolition and excavation) (esriGeometryPoint, NEW)
- WASTE2026 716 HIC — Waste transfer (household and commercial) (esriGeometryPoint, NEW)
- WASTE2026 70 HIC — Sites <= 15,000 tonnes (esriGeometryPoint, NEW)
- WASTE2026 730 Inert — Disposal (esriGeometryPoint, NEW)
- WASTE2026 729 Inert — Disposal (inert) (esriGeometryPoint, NEW)
- WASTE2026 728 Inert — Fuel preparation and MBT (esriGeometryPoint, NEW)
- WASTE2026 726 Inert — Materials recycling and sorting (esriGeometryPoint, NEW)
- WASTE2026 725 Inert — Metals and vehicle recycling (esriGeometryPoint, NEW)
- WASTE2026 731 Inert — Other (esriGeometryPoint, NEW)
- WASTE2026 732 Inert — Other (inert) (esriGeometryPoint, NEW)
- WASTE2026 721 Inert — Transfer and treatment (construction, demolition and excavation) (esriGeometryPoint, NEW)
- WASTE2026 720 Inert — Waste transfer (household and commercial) (esriGeometryPoint, NEW)
- WASTE2026 50 Inert — Sites <= 15,000 tonnes (esriGeometryPoint, NEW)
- WASTE2026 738 Hazardous — Materials recycling and sorting (esriGeometryPoint, NEW)
- WASTE2026 737 Hazardous — Metals and vehicle recycling (esriGeometryPoint, NEW)
- WASTE2026 736 Hazardous — Other (esriGeometryPoint, NEW)
- WASTE2026 734 Hazardous — Transfer and treatment (construction, demolition and excavation) (esriGeometryPoint, NEW)
- WASTE2026 23 Hazardous — Sites <= 15,000 tonnes (esriGeometryPoint, NEW)
- WASTE2026 739 EA Waste Sites 2013-2024 (esriGeometryPoint, NEW)
- WASTE2026 17 Air Quality Management Areas (esriGeometryPolygon, NEW)
- WASTE2026 18 Waste Authorities Planning Groups (esriGeometryPolygon, NEW)
- WASTE2026 12 Opportunity Areas (esriGeometryPolygon, MIRROR)
- WASTE2026 13 Housing Zones (esriGeometryPolygon, MIRROR)
- WASTE2026 14 Safeguarded Wharves (esriGeometryPolygon, MIRROR)
- WASTE2026 0 London Borough (esriGeometryPolygon, MIRROR)
- WASTE2026 15 GLA Boundary (esriGeometryPolygon, MIRROR)

Every request used the official MapServer layer `/query` endpoint with `where=1=1`, EPSG:3857 candidate point geometry, `esriSpatialRelIntersects`, `returnIdsOnly=true`, and `f=json`. All requests ended before a usable response body. No membership, proximity, licence, capacity or delivery inference was made.