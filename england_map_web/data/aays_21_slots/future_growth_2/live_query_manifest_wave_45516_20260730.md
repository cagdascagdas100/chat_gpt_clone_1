# future_growth_2 live official query manifest

Continuation key: `5c59c5cee91d859c9e09480645ef8b17efe264568f2a4e312dd49d70e2958462`
Generated: `2026-07-30T20:28:00+03:00`

Read-only official ArcGIS `returnIdsOnly` point-intersects queries. Transport failure is not interpreted as a positive or negative result.

Transport: 54 attempts; parallelism 54; exit 6 x54; HTTP 000 x54; body bytes 0; JSON 0/54; raw-response SHA-256 0/54.

Query manifest SHA-256: `6af5d24b04b7f7afe5dc434dd1f6edd2b5514bbc8a05c5c6dfd3c8cc68791ffb`
Transport results SHA-256: `be2986bace2441dd6368855d8b652bd4ba5ab2354e250434bf3bb9215d150278`

Layers crossed with rows 30762, 46142 and 61522:
- WEBCTX 0 London GLA boundary (esriGeometryPolygon, NEW)
- WEBCTX 12 London Planning Authority (esriGeometryPolygon, NEW)
- WEBCTX 10 London Planning Authority (Pre-Dec 2024) (esriGeometryPolygon, MIRROR)
- WEBCTX 3 London Borough (esriGeometryPolygon, NEW)
- WEBCTX 7 London Assembly Constituencies (esriGeometryPolygon, NEW)
- WEBCTX 14 London Westminster Constituencies (esriGeometryPolygon, NEW)
- WEBCTX 15 London MPS Basic Command Units (esriGeometryPolygon, NEW)
- WEBCTX 6 OPDC (esriGeometryPolygon, NEW)
- WEBCTX 13 LLDC (esriGeometryPolygon, NEW)
- WEBCTX 11 LLDC (Pre-Dec 2024) (esriGeometryPolygon, MIRROR)
- WEBCTX 1 River Thames (esriGeometryPolygon, NEW)
- WEBCTX 4 TfL 350m Hexagon Grid (esriGeometryPolygon, NEW)
- WEBCTX 5 London Wards (2021) (esriGeometryPolygon, MIRROR)
- WEBCTX 8 London LSOA (2021) (esriGeometryPolygon, NEW)
- WEBCTX 9 London Wards (2022) (esriGeometryPolygon, MIRROR)
- WEBCTX 18 London Wards (2025) (esriGeometryPolygon, NEW)
- WEBCTX 17 Oxford Street Mayoral Development Area (esriGeometryPolygon, NEW)
- WEBCTX 16 Index of Multiple Deprivation 2025 (esriGeometryPolygon, NEW)

Every request used the official layer `/query` endpoint with `where=1=1`, EPSG:27700 point geometry, `esriSpatialRelIntersects`, `returnIdsOnly=true`, and `f=json`. No membership inference was made from transport failure.

Pre-Dec 2024 planning-authority/LLDC and 2021/2022 ward layers were retained only as temporal comparisons and were not double-counted as new bindings or exact negatives.