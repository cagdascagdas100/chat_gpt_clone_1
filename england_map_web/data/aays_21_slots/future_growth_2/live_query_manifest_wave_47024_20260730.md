# future_growth_2 live official query manifest

Continuation key: `5c59c5cee91d859c9e09480645ef8b17efe264568f2a4e312dd49d70e2958462`
Generated: `2026-07-30T21:18:00+03:00`

Read-only official ArcGIS `returnIdsOnly` point-intersects queries. Transport failure is not interpreted as a positive or negative result.

Transport: 84 attempts; parallelism 84; exit counts {"28": 78, "6": 6}; HTTP counts {"000": 84}; body bytes 0; JSON 0/84; raw-response SHA-256 0/84.

Query manifest SHA-256: `1f4a9d4712e9d5362895bd8e4305edbdce30bb8e2bbdc20dd153e83d082c2bd4`
Transport results SHA-256: `37d9b77422eb72aefc7ddf027cf249866898481f1ba9e4c10fb0cddcf7d1f9bd`

Layers crossed with rows 30762, 46142 and 61522:
- GGF 0 Hex - for filtering (esriGeometryPolygon, AGGREGATE)
- GGF 1 GGF Rounds 1-3, successful (esriGeometryPoint, NEW)
- GGF 3 Environment Programmes 2016-22 (esriGeometryPoint, NEW)
- GGF 4 GRSF delivery sites (esriGeometryPoint, NEW)
- GGF 5 Hex - worst 20% IMD, open space & climate risk (esriGeometryPolygon, NEW)
- GGF 6 Creative Enterprise Zones (esriGeometryPolygon, NEW)
- GGF 8 Opportunity Areas - Adopted boundary (esriGeometryPolygon, MIRROR)
- GGF 9 Opportunity Areas - Emerging boundary (esriGeometryPolygon, NEW)
- GGF 10 Opportunity Areas - Boundary to be defined (esriGeometryPolygon, NEW)
- GGF 27 Growth Corridors - outline (esriGeometryPolygon, REPRESENTATION)
- GGF 50 Growth Corridors - fill (esriGeometryPolygon, MIRROR)
- GGF 28 Hex - cluster of planning commencements (esriGeometryPolygon, NEW)
- GGF 29 Cultural Audience - least participation (esriGeometryPolygon, NEW)
- GGF 31 IMD | 2019 (esriGeometryPolygon, MIRROR)
- GGF 32 Hex - residential commencements 2017-22 (esriGeometryPolygon, NEW)
- GGF 33 Hex - Overall Climate Risk - worst 20% (esriGeometryPolygon, NEW)
- GGF 34 Hex - tree cover (esriGeometryPolygon, NEW)
- GGF 36 Cultural Audience Segmentation (esriGeometryPolygon, NEW)
- GGF 37 Open Space (>10Ha) (esriGeometryPolygon, NEW)
- GGF 51 Urban Villages - top 25 change & need (esriGeometryPolygon, NEW)
- GGF 14 Urban Villages - change (esriGeometryPolygon, REPRESENTATION)
- GGF 13 Urban Villages - investment (esriGeometryPolygon, REPRESENTATION)
- GGF 12 Urban Villages - need (esriGeometryPolygon, REPRESENTATION)
- GGF 40 Urban Villages (esriGeometryPolygon, NEW)
- GGF 42 TfL - priorities for LTNs (esriGeometryPolygon, NEW)
- GGF 43 Civic Strength Index (lowest 20%) (esriGeometryPolygon, REPRESENTATION)
- GGF 44 Civic Strength Index (Wards) (esriGeometryPolygon, NEW)
- GGF 45 London Borough (esriGeometryPolygon, MIRROR)

Every request used the official layer `/query` endpoint with `where=1=1`, EPSG:27700 point geometry, `esriSpatialRelIntersects`, `returnIdsOnly=true`, and `f=json`. No membership inference was made from transport failure.

Point extents, aggregate filters, mirrors and same-extent representation layers were not counted as parcel proximity, membership or duplicate exact negatives.