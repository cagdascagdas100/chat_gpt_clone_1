# future_growth_2 live official query manifest

Continuation key: `5c59c5cee91d859c9e09480645ef8b17efe264568f2a4e312dd49d70e2958462`
Generated: `2026-07-30T17:57:00+03:00`

Read-only official ArcGIS `returnIdsOnly` point-intersects queries. Transport failure is not interpreted as a positive or negative result.

Transport: 36 attempts; parallelism 36; exit 6 x36; HTTP 000 x36; body bytes 0; JSON 0/36; raw-response SHA-256 0/36.

Layers crossed with rows 30762, 46142 and 61522:
- UTCF 1 GP 50m buffer (NEW)
- UTCF 2 Hospital 50m buffer (NEW)
- UTCF 3 School 50m buffer (NEW)
- UTCF 9 World Heritage Site (NEW)
- UTCF 10 Sites of Special Scientific Interest (SSSI) (COMPARISON)
- UTCF 12 Scheduled monument (NEW)
- UTCF 14 RSPB Important Bird Areas (NEW)
- UTCF 15 Registered Parks and Gardens (Graded) (MIRROR)
- UTCF 16 Local Nature Reserve (NEW)
- UTCF 17 CRoW 2000 (Countryside Rights of Way) (NEW)
- UTCF 20 Ancient Woodland (NEW)
- UTCF 21 Sites of Importance for Nature Conservation (SINC) (NEW)

Every request used the official FeatureServer layer `/query` endpoint with `where=1=1`, EPSG:27700 candidate point geometry, `esriSpatialRelIntersects`, `returnIdsOnly=true`, and `f=json`. All requests ended before a usable response body: exit 6, HTTP 000, 0 bytes. No membership inference was made.

Query manifest SHA-256: `3a191c2ebb351d6b8c9d5768e60fbf27fff2f0574bbf565c7aa998fa234bc8cc`
Transport results SHA-256: `81bfdb4058610da200c1642c3cf82d7aceef2fc32d71f894baf0d7490e7db100`
