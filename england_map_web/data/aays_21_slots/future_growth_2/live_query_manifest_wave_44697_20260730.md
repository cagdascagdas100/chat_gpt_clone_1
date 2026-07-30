# future_growth_2 live official query manifest

Continuation key: `5c59c5cee91d859c9e09480645ef8b17efe264568f2a4e312dd49d70e2958462`
Generated: `2026-07-30T20:14:04+03:00`

Read-only official ArcGIS `returnIdsOnly` point-intersects queries. Transport failure is not interpreted as a positive or negative result.

Transport: 66 attempts; parallelism 66; exit 6 x66; HTTP 000 x66; body bytes 0; JSON 0/66; raw-response SHA-256 0/66.

Query manifest SHA-256: `34711e0417754f16f7830985e5b0864b83fba11419e68ee6390093ac7fe81487`
Transport results SHA-256: `0d845349ae0e059b4e043a2a6807bbb55cd3151e3c5d1dccc6c4c51bb5337b6e`

Layers crossed with rows 30762, 46142 and 61522:
- PDM 101 Brownfield Register (esriGeometryPolygon, NEW)
- PDM 102 Site Allocations (esriGeometryPolygon, NEW)
- PDM 106 Areas of Intensification (esriGeometryPolygon, NEW)
- PDM 107 Central Activities Zone (esriGeometryPolygon, NEW)
- PDM 109 MCIL2 Charging Area (esriGeometryPolygon, NEW)
- PDM 110 MCIL2 Charging Bands (esriGeometryPolygon, AGGREGATE)
- PDM 111 MCIL2 Charging Band 1 (esriGeometryPolygon, NEW)
- PDM 112 MCIL2 Charging Band 2 (esriGeometryPolygon, NEW)
- PDM 113 MCIL2 Charging Band 3 (esriGeometryPolygon, NEW)
- PDM 205 Conservation Areas (esriGeometryPolygon, NEW)
- PDM 206 Strategic Industrial Land (SIL) (esriGeometryPolygon, NEW)
- PDM 207 Locally Significant Industrial Sites (LSIS) (esriGeometryPolygon, NEW)
- PDM 210 Designated Open Space (GreenBelt) (esriGeometryPolygon, NEW)
- PDM 211 Designated Open Space (Metropolitan Open Land) (esriGeometryPolygon, NEW)
- PDM 212 Designated Open Space (Other Open Space) (esriGeometryPolygon, NEW)
- PDM 213 Protected Vistas (esriGeometryPolygon, NEW)
- PDM 215 Protected Vistas (Viewing Corridor) (esriGeometryPolygon, REPRESENTATION)
- PDM 216 Protected Vistas (Wider Setting Consultation Area) (esriGeometryPolygon, REPRESENTATION)
- PDM 220 Protected Vistas (Extension) (esriGeometryPolygon, REPRESENTATION)
- PDM 218 Thames Policy Area (Mayor of London) (esriGeometryPolygon, NEW)
- PDM 219 Thames Policy Area (LPA) (esriGeometryPolygon, NEW)
- PDM 223 Critical Drainage Areas (esriGeometryPolygon, NEW)

Every request used the official MapServer layer `/query` endpoint with `where=1=1`, EPSG:27700 point geometry, `esriSpatialRelIntersects`, `returnIdsOnly=true`, and `f=json`. No membership inference was made from transport failure.

Identical Protected Vistas declared extents were deduplicated for exact-negative accounting; aggregate MCIL2 layer 110 was not treated as a new site binding.