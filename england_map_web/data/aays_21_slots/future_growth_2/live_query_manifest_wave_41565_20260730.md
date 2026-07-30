# future_growth_2 live official query manifest

Continuation key: `5c59c5cee91d859c9e09480645ef8b17efe264568f2a4e312dd49d70e2958462`
Generated: `2026-07-30T17:32:00+03:00`

Read-only official ArcGIS `returnIdsOnly` point-intersects queries. Transport failure is not interpreted as a positive or negative result.

Transport: 27 attempts; parallelism 27; exit 6 x27; HTTP 000 x27; body bytes 0; JSON 0/27; raw-response SHA-256 0/27.

Layers crossed with rows 30762, 46142 and 61522:
- CULT 2 London boroughs
- CULT 24 Safeguarded wharves
- CULT 33 cultural ticket participation 2016/17
- CULT 34 Indices of Multiple Deprivation 2019
- CULT 40 GiGL greenspace
- PARKS 0 Spaces to Visit 2025
- PARKS 1 Registered Parks and Gardens
- DEFRA 4 SSSI
- UTCF 11 SPA

Every request used the official layer `/query` endpoint with `where=1=1`, EPSG:27700 candidate point geometry, `esriSpatialRelIntersects`, `returnIdsOnly=true`, and `f=json`. All 27 requests ended before a usable response body: exit 6, HTTP 000, 0 bytes. No membership inference was made.

Query manifest SHA-256: `0ad6c29aeaa82d7e6f4f862330a015876fb9a4781f8f0700cfbd2bbd14f7275a`
Transport results SHA-256: `3be69e4036e10d9bac82b0aa31d92edaff555ffdb36f428fad236cc6a1712758`
