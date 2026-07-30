# future_growth_2 live official query manifest

Continuation key: `5c59c5cee91d859c9e09480645ef8b17efe264568f2a4e312dd49d70e2958462`
Generated: `2026-07-30T18:53:32+03:00`

Read-only official ArcGIS `returnIdsOnly` point-intersects queries. Transport failure is not interpreted as a positive or negative result.

Transport: 48 attempts; parallelism 48; exit 6 x48; HTTP 000 x48; body bytes 0; JSON 0/48; raw-response SHA-256 0/48.

Query manifest SHA-256: `514d6d0e619360f394833888d414a84e6ea863a4e3310b94dca4b7d17e1ec1ae`
Transport results SHA-256: `1b9b20bdfe1cb503adaa615af4440bfc904a61214d2dddc7633d47016fd90868`

Candidate coordinates were transformed from EPSG:27700 to EPSG:3857. Each of the 16 layers was queried for rows 30762, 46142 and 61522.

- IMA 0 TfL Road Network (TLRN) (esriGeometryPolyline, NEW)
- IMA 1 TfL Lane Rental (esriGeometryPolyline, NEW)
- IMA 2 Town Centre Boundaries (esriGeometryPolygon, MIRROR)
- IMA 3 Public Transport Accessibility (esriGeometryPolygon, NEW)
- IMA 4 London Boroughs (esriGeometryPolygon, MIRROR)
- IMA 5 Housing Zones (esriGeometryPolygon, MIRROR)
- IMA 6 Business Improvement Districts (esriGeometryPolygon, NEW)
- IMA 7 Adopted Opportunity Areas (esriGeometryPolygon, MIRROR)
- IMA 8 Strategic Industrial Land (SIL) (esriGeometryPolygon, MIRROR)
- IMA 9 Strategic Housing Land Availability Assessment (SHLAA) (esriGeometryPolygon, MIRROR)
- IMA 10 Growth Corridors (esriGeometryPolygon, NEW)
- IMA 11 High Street Boundaries (esriGeometryPolygon, NEW)
- IMA 12 Utility Coverage Areas: Power (esriGeometryPolygon, NEW)
- IMA 13 Utility Coverage Areas: Water (esriGeometryPolygon, NEW)
- IMA 14 Utility Coverage Areas: Sewerage (esriGeometryPolygon, NEW)
- IMA 15 Utility Coverage Areas: Gas (esriGeometryPolygon, NEW)

Every request used the official layer `/query` endpoint with `where=1=1`, EPSG:3857 point geometry, `esriSpatialRelIntersects`, `returnIdsOnly=true`, and `f=json`. All requests ended before a usable body; no membership inference was made.
