# future_growth_2 live official query manifest

Continuation key: `5c59c5cee91d859c9e09480645ef8b17efe264568f2a4e312dd49d70e2958462`
Generated: `2026-07-30T19:38:00+03:00`

Read-only official ArcGIS `returnIdsOnly` point-intersects queries. Transport failure is not interpreted as a positive or negative result.

Transport: 66 attempts; parallelism 66; exit counts {"6": 66}; HTTP counts {"000": 66}; body bytes 0; JSON 0/66; raw-response SHA-256 0/66.

Query manifest SHA-256: `00dd3cdf9b37991620b06e547072eb0c7f293454f36d8d3907d0330bd01e2626`
Transport results SHA-256: `bd1d4151277a0c9e52b2c1a23c08b302a544dff357483d8b7df0d17fcb89b0e5`

Layers crossed with rows 30762, 46142 and 61522:
- PROFILE 5 <30Mbit/s (esriGeometryPolygon, NEW)
- PROFILE 7 Concentration of residents 65+ | 2011 | Census (esriGeometryPolygon, NEW)
- PROFILE 8 Concentration of residents 65+ | 2019 | ONS (esriGeometryPolygon, NEW)
- PROFILE 9 Concentration of residents 75+ | 2019 | ONS (esriGeometryPolygon, NEW)
- PROFILE 10 IMD - affecting older people | 2019 (esriGeometryPolygon, NEW)
- PROFILE 12 Income Deprivation Affecting Children | 2019 (esriGeometryPolygon, NEW)
- PROFILE 13 Free School Meals | 2017 | DfE (esriGeometryPolygon, NEW)
- PROFILE 15 JSA claimants | 2019 | DWP (esriGeometryPolygon, NEW)
- PROFILE 16 JSA claimants | 2021 | DWP (esriGeometryPolygon, NEW)
- PROFILE 17 IMD - employment | 2019 (esriGeometryPolygon, NEW)
- PROFILE 19 Small Area Mental Health Index | 2018 (esriGeometryPolygon, NEW)
- PROFILE 20 Disability Living Allowance | 2018 | DWP (esriGeometryPolygon, NEW)
- PROFILE 22 microbusinesses | 2019 | ONS (esriGeometryPolygon, NEW)
- PROFILE 23 microbusinesses | 2019 | ONS — alternate representation (esriGeometryPolygon, MIRROR)
- PROFILE 25 Census 2021 Paper returns (esriGeometryPolygon, NEW)
- PROFILE 27 London Output Area Classification (LOAC) — group (esriGeometryPolygon, NEW)
- PROFILE 28 London Output Area Classification (LOAC) — supergroup (esriGeometryPolygon, MIRROR)
- PROFILE 29 Internet Use Classification - 2018 — class breaks (esriGeometryPolygon, NEW)
- PROFILE 30 Internet Use Classification - 2018 — labels (esriGeometryPolygon, MIRROR)
- FUTURE 36 London Development Database (esriGeometryPoint, NEW)
- FUTURE 37 projected population growth (esriGeometryPolygon, NEW)
- FUTURE 38 projected Job Growth (esriGeometryPolygon, NEW)

Every request used the official layer `/query` endpoint with `where=1=1`, EPSG:27700 point geometry, `esriSpatialRelIntersects`, `returnIdsOnly=true`, and `f=json`. No membership inference was made from transport failure.
